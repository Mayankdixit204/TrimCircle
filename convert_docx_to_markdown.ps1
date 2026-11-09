param(
    [Parameter(Mandatory = $true)][string]$InputDocx,
    [Parameter(Mandatory = $true)][string]$OutputMarkdown
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Escape-MarkdownCell([string]$Text) {
    if ($null -eq $Text) { return '' }
    return ($Text -replace '\|', '\|' -replace "`r?`n", '<br>')
}

function Get-NodeText($Node, $NamespaceManager) {
    $parts = foreach ($child in $Node.SelectNodes('.//w:t | .//w:tab | .//w:br', $NamespaceManager)) {
        if ($child.LocalName -eq 't') { $child.InnerText }
        elseif ($child.LocalName -eq 'tab') { "`t" }
        else { "  `n" }
    }
    return ($parts -join '')
}

$archive = [System.IO.Compression.ZipFile]::OpenRead($InputDocx)
try {
    $entry = $archive.GetEntry('word/document.xml')
    if ($null -eq $entry) { throw 'The DOCX does not contain word/document.xml.' }

    $reader = [System.IO.StreamReader]::new($entry.Open())
    try { [xml]$xml = $reader.ReadToEnd() } finally { $reader.Dispose() }

    $ns = [System.Xml.XmlNamespaceManager]::new($xml.NameTable)
    $ns.AddNamespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
    $body = $xml.SelectSingleNode('//w:body', $ns)
    $lines = [System.Collections.Generic.List[string]]::new()

    foreach ($node in $body.ChildNodes) {
        if ($node.LocalName -eq 'p') {
            $text = (Get-NodeText $node $ns).Trim()
            if ([string]::IsNullOrWhiteSpace($text)) {
                if ($lines.Count -gt 0 -and $lines[$lines.Count - 1] -ne '') { $lines.Add('') }
                continue
            }

            $styleNode = $node.SelectSingleNode('./w:pPr/w:pStyle', $ns)
            $style = if ($styleNode) { $styleNode.GetAttribute('val', $ns.LookupNamespace('w')) } else { '' }
            $numNode = $node.SelectSingleNode('./w:pPr/w:numPr', $ns)

            if ($style -match '^Title$') { $lines.Add("# $text") }
            elseif ($style -match '^Heading([1-6])$') { $lines.Add((('#' * [int]$Matches[1]) + " $text")) }
            elseif ($numNode) {
                $levelNode = $numNode.SelectSingleNode('./w:ilvl', $ns)
                $level = if ($levelNode) { [int]$levelNode.GetAttribute('val', $ns.LookupNamespace('w')) } else { 0 }
                $lines.Add((('  ' * $level) + "- $text"))
            }
            else { $lines.Add($text) }
            $lines.Add('')
        }
        elseif ($node.LocalName -eq 'tbl') {
            $rows = @($node.SelectNodes('./w:tr', $ns))
            if ($rows.Count -eq 0) { continue }
            $table = foreach ($row in $rows) {
                ,@($row.SelectNodes('./w:tc', $ns) | ForEach-Object {
                    Escape-MarkdownCell ((Get-NodeText $_ $ns).Trim())
                })
            }
            $columnCount = ($table | ForEach-Object { $_.Count } | Measure-Object -Maximum).Maximum
            $header = @($table[0]) + @('' * [Math]::Max(0, $columnCount - $table[0].Count))
            $lines.Add('| ' + (($header | ForEach-Object { $_ }) -join ' | ') + ' |')
            $lines.Add('| ' + ((1..$columnCount | ForEach-Object { '---' }) -join ' | ') + ' |')
            foreach ($row in ($table | Select-Object -Skip 1)) {
                $cells = @($row) + @('' * [Math]::Max(0, $columnCount - $row.Count))
                $lines.Add('| ' + (($cells | ForEach-Object { $_ }) -join ' | ') + ' |')
            }
            $lines.Add('')
        }
    }

    while ($lines.Count -gt 0 -and $lines[$lines.Count - 1] -eq '') { $lines.RemoveAt($lines.Count - 1) }
    $outputDirectory = Split-Path -Parent $OutputMarkdown
    if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory | Out-Null
    }
    [System.IO.File]::WriteAllLines($OutputMarkdown, $lines, [System.Text.UTF8Encoding]::new($false))
}
finally {
    $archive.Dispose()
}
