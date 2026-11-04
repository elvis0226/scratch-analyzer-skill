# 工具用法

Python 3 可直接執行稽核與文字轉換。渲染需要 Node.js、Playwright、scratchblocks 和 Chrome。依 [安裝說明](../README.md) 準備套件。以下 PowerShell 命令假設目前位於使用者的作品工作區。

```powershell
$Skill = '安裝後的 scratch-analyzer 資料夾絕對路徑'
$Source = '原始檔.sb3'
$Check = 'output/作品識別碼/check'
python -X utf8 "$Skill/scripts/validate_project.py" $Source --out $Check
# 上一步成功才執行整批匯出。
python -X utf8 "$Skill/scripts/export_project.py" $Source --out $Check
```

- `validate_project.py` 檢查 ZIP、素材、連線及文字轉換。退出碼 0 為文字通過，1 為封裝或結構問題，2 為腳本轉換受阻。參考終端訊息與 `validation.json`。
- `export_project.py` 整批產生 TXT、繁中 SVG、`scripts-manifest.json` 與技術預覽 `preview.html`。有受阻項目時整批會停止，渲染失敗也可能留下部分檔案。請對照本次來源與產物後再交付。
- 有可獨立核對的腳本時，使用下列單支方式。PowerShell 以 .NET 寫入 UTF-8，以免舊版 PowerShell 重新導向改變編碼。

```powershell
$Target = '來源角色名稱'
$Block = '頂層 block ID'
$Txt = Join-Path $Check 'target-01-script-01.txt'
$Svg = Join-Path $Check 'target-01-script-01.svg'
$Lines = python -X utf8 "$Skill/scripts/sb3_to_scratchblocks.py" $Source --sprite $Target --block-id $Block
if ($LASTEXITCODE -eq 0) {
    [IO.File]::WriteAllLines((Join-Path (Get-Location).Path $Txt), [string[]]$Lines, [Text.UTF8Encoding]::new($false))
    node "$Skill/scripts/render_svg.cjs" $Txt $Svg zh-tw
}
```

可用 `export_fragments.py SOURCE CONFIG --out DIRECTORY` 匯出片段。CONFIG 結構為 `{"sprite":"角色","fragments":[{"slug":"detail-loop","block_id":"來源 ID"}]}`。匯出從選取積木沿 `next` 到末尾。擷取較短片段時，按已核對的積木邊界截取，重建實際涵蓋的 ID 清單。工具可能為獨立條件加空「如果」外框，應依片段紀錄標示。

使用絕對路徑的 Python 或 Node 時，可替換命令，並用 `--node` 指定 Python 匯出器要呼叫的 Node。既有工具負責技術輸出，總覽、詳情與挑戰頁由 Codex 按規格製作。可用 Scratch 桌面版或使用者已有的 Scratch VM 實測原檔。
