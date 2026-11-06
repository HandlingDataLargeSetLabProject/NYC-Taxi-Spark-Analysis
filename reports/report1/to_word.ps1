# Turn the report HTML into .docx and .pdf with Microsoft Word: embed the images, add the table of
# contents and page numbers, and set the document properties. Called by build_report.py.
param(
    [Parameter(Mandatory)] [string] $Html,
    [Parameter(Mandatory)] [string] $Docx,
    [Parameter(Mandatory)] [string] $Pdf,
    [Parameter(Mandatory)] [string] $Title,
    [Parameter(Mandatory)] [string] $Author
)
$ErrorActionPreference = "Stop"

$WdFormatDocumentDefault = 16
$WdExportFormatPdf = 17
$WdExportCreateHeadingBookmarks = 1
$WdPrintView = 3
$WdAlignPageNumberCenter = 1

function Set-DocumentProperty($Document, [string] $Name, [string] $Value) {
    $properties = $Document.BuiltInDocumentProperties
    $property = [System.__ComObject].InvokeMember("Item", "GetProperty", $null, $properties, @($Name))
    [System.__ComObject].InvokeMember("Value", "SetProperty", $null, $property, @($Value)) | Out-Null
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $document = $word.Documents.Open($Html, $false, $true)
    $document.ActiveWindow.View.Type = $WdPrintView

    # Pictures from HTML are only linked; store them inside the file so the report works on its own.
    foreach ($shape in @($document.InlineShapes)) {
        if ($null -ne $shape.LinkFormat) {
            $shape.LinkFormat.SavePictureWithDocument = $true
            $shape.LinkFormat.BreakLink()
        }
    }

    # Word gives table cells the spacing of HTML paragraphs, which makes every row twice as tall.
    foreach ($table in @($document.Tables)) {
        $table.Range.ParagraphFormat.SpaceBefore = 0
        $table.Range.ParagraphFormat.SpaceAfter = 0
    }

    $marker = $document.Content
    if ($marker.Find.Execute("[[TOC]]")) {
        $marker.Text = ""
        $document.TablesOfContents.Add($marker, $true, 1, 2) | Out-Null
    }

    $footer = $document.Sections.Item(1).Footers.Item(1)
    $footer.PageNumbers.Add($WdAlignPageNumberCenter, $false) | Out-Null
    $document.PageSetup.DifferentFirstPageHeaderFooter = $true

    Set-DocumentProperty $document "Title" $Title
    Set-DocumentProperty $document "Author" $Author
    Set-DocumentProperty $document "Last author" $Author

    $document.TablesOfContents.Item(1).Update()
    $document.SaveAs2($Docx, $WdFormatDocumentDefault)
    $document.ExportAsFixedFormat($Pdf, $WdExportFormatPdf, $false, 0, 0, 1, 1, 0, $true, $true, $WdExportCreateHeadingBookmarks)
    $document.Close($false)
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
