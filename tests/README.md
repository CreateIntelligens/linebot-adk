# 單元測試說明

這個目錄包含了 LINE Bot ADK 專案的所有單元測試。

## 測試檔案

### test_main.py
測試 `main.py` 中的主要功能：
- 會話管理 (`get_or_create_session`, `push_message_to_user`)
- 訊息處理 (`create_reply_messages`)
- 環境變數驗證

### 專門 Agent 測試檔案

#### test_weather_agent.py
測試天氣查詢功能：
- WeatherAgent 類別方法
- 天氣查詢和預報 API 整合
- 錯誤處理和降級方案

#### test_legal_agent.py
測試法律諮詢功能：
- 法律問題分類 (`classify_legal_question`)
- AI 法律諮詢 (`legal_ai`)
- 備用法律諮詢服務 (`fallback_legal`)
- 合約、糾紛、研究、企業法務等分類

#### test_meme_agent.py
測試 Meme 生成功能：
- Meme 文字生成 (`generate_meme_text`)
- 模板選擇 (`select_meme_template`)
- ImgFlip API 整合 (`create_meme_imgflip`)
- 備用生成服務

#### test_comfyui_agent.py
測試 AI 影片生成功能：
- ComfyUI 客戶端操作
- 模板載入和修改
- 工作提交和狀態檢查
- 影片資訊提取和下載

#### test_agent_functions.py
測試主要 agent 包裝函數：
- 時間查詢 (`get_current_time`)
- 知識庫查詢 (`query_knowledge_base`, `query_set_knowledge_base`)
- 短網址生成 (`create_short_url`)
- 影片處理 (`process_video`, `get_task_status`)
- 工具函數 (`before_reply_display_loading_animation`)

### test_agents.py (已棄用)
舊的綜合測試檔案，保留以供參考。

### run_tests.py
測試運行腳本，用於批量執行所有測試。

## 如何運行測試

### 在 Docker 環境中運行

```bash
# 進入容器
docker-compose exec app bash

# 運行所有測試（自動選擇框架）
python tests/run_tests.py

# 或使用 pytest 直接運行
python -m pytest tests/ -v

# 或使用 unittest 直接運行
python -m unittest discover -s tests/
```

### 在本地環境中運行

```bash
# 安裝依賴
pip install -r requirements.txt

# 安裝測試依賴（推薦）
pip install -r tests/requirements-test.txt

# 運行所有測試（自動選擇框架）
python tests/run_tests.py

# 使用 pytest 運行（推薦）
pytest tests/ -v
pytest tests/test_weather_agent.py -v
pytest tests/test_legal_agent.py::TestLegalAI::test_legal_ai_success_contract -v

# 使用 pytest 運行特定標記的測試
pytest tests/ -m "not slow"  # 排除慢速測試
pytest tests/ -k "weather"   # 只運行包含 "weather" 的測試

# 或使用 unittest 運行
python -m unittest tests.test_main
python -m unittest tests.test_agents
```

### Pytest 進階用法

```bash
# 生成覆蓋率報告
pytest tests/ --cov=multi_tool_agent --cov-report=html

# 運行特定類別的測試
pytest tests/test_legal_agent.py::TestLegalQuestionClassification -v

# 運行帶有特定標記的測試
pytest tests/ -m asyncio  # 只運行非同步測試

# 詳細輸出
pytest tests/ -v -s --tb=long

# 並行運行（需要安裝 pytest-xdist）
pip install pytest-xdist
pytest tests/ -n auto
```

## 測試覆蓋的功能

### 天氣功能
- ✅ 當前天氣查詢
- ✅ 天氣預報查詢
- ✅ API 錯誤處理

### 法律諮詢
- ✅ 問題分類（合約、糾紛、研究、企業、一般）
- ✅ AI 法律諮詢
- ✅ 備用諮詢服務

### Meme 生成
- ✅ AI 生成 meme 文字
- ✅ 智能選擇模板
- ✅ ImgFlip API 整合
- ✅ 備用生成服務

### AI 影片生成
- ✅ ComfyUI 模板載入
- ✅ 文字內容修改
- ✅ 工作提交和監控

### 主要功能
- ✅ 短網址生成
- ✅ 影片處理
- ✅ 任務狀態查詢
- ✅ 時間查詢
- ✅ 知識庫查詢

## 測試策略

### Mock 策略
- 使用 `unittest.mock` 模擬外部 API 呼叫
- 避免依賴真實網路服務
- 測試錯誤處理和邊界情況

### 非同步測試
- 使用 `asyncio` 測試非同步函數
- 適當處理事件循環

### 環境變數
- 測試中動態設定和清理環境變數
- 避免影響其他測試

## 測試品質指標

- **覆蓋率**: 涵蓋所有主要 agent 功能
- **可靠性**: 使用 mock 避免外部依賴
- **可維護性**: 清晰的測試結構和註釋
- **執行速度**: 快速的單元測試套件

## 新增測試

### 為新功能新增測試
1. 在適當的測試類別中新增測試方法
2. 使用描述性的方法名稱（`test_feature_name_scenario`）
3. 添加適當的 docstring
4. 使用 mock 處理外部依賴

### 測試命名慣例
```python
def test_function_name_success_case(self):
    """測試函數名稱 - 成功情況"""

def test_function_name_error_case(self):
    """測試函數名稱 - 錯誤情況"""
```

## 持續整合

這些測試可以在 CI/CD 流程中自動運行：

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    docker-compose up -d
    docker-compose exec -T app python tests/run_tests.py
```

## 故障排除

### 常見問題

1. **ImportError**: 確保 Python 路徑正確設定
2. **Mock 失敗**: 檢查 mock 目標的模組路徑
3. **環境變數**: 確保測試中正確設定和清理環境變數

### 除錯技巧

```python
# 啟用詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)

# 檢查模組路徑
print(sys.path)
```

---

如有問題或需要新增測試，請參考現有測試的模式和結構。
