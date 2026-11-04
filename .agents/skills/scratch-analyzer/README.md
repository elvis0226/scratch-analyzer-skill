# Scratch 檔案分析師

把 Scratch 3 的 `.sb3` 交給 Codex，取得完整腳本索引、繁體中文積木圖、重點解說及可離線瀏覽的分析頁。唯一範例是[旋轉出美麗的花朵](assets/example/index.html)。下載整個資料夾後，用瀏覽器開啟範例的 `index.html`。

## 安裝

1. 從 GitHub 下載這個儲存庫或用 Git 複製。直接用 Codex 開啟儲存庫時，技能位於 `.agents/skills/scratch-analyzer`。若要在其他工作區使用，將整個 `scratch-analyzer` 資料夾複製到目標工作區的 `.agents/skills/`，或使用者家目錄的 `.agents/skills/`。
2. 確認有 Python 3、Node.js 20 以上、npm 與 Chrome。用終端機進入包含 `SKILL.md` 的技能資料夾，執行 `npm install --ignore-scripts --no-audit --no-fund`。初次安裝套件需要網路，後續稽核、渲染及閱讀產物可在本機離線進行。
3. 開啟新的 Codex 聊天，附上原始 `.sb3`，輸入下列提示。若技能清單未更新，重新開啟工作區。

> 用 $scratch-analyzer 分析我附上的 Scratch 3 原始檔。請依完整索引與重點解說製作離線分析頁，保留來源對照並交付待審草稿。

技能位置與安裝方式參考 [OpenAI 官方技能文件](https://learn.chatgpt.com/docs/build-skills)。

## 確認環境

從技能資料夾執行下列命令，可用唯一範例重跑稽核及繁中圖像匯出。若 Chrome 裝在非標準位置，先將 `CHROME_PATH` 設為 Chrome 執行檔的絕對路徑。

```text
python -X utf8 scripts/validate_project.py assets/example/original.sb3 --out output/smoke-check
python -X utf8 scripts/export_project.py assets/example/original.sb3 --out output/smoke-check
```

預期有一支綠旗腳本、八個來源積木。新產物中的 `preview.html` 是技術預覽。分析頁、答題與來源對照可查閱範例。
