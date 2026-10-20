# 航空促銷（promos.json）

「最新優惠」分頁最上方的「航空促銷」卡片讀的是網站根目錄的 `promos.json`。這和 `deals.json` 裡的便宜機票（`promos` 陣列）是兩份資料。更新促銷時只改 `promos.json`，不要改 `deals.json`、`tp_prices.json` 或查價流程。

卡片只出現在「最新優惠」裡，查機票頁不另外放一條促銷列。`bookTo` 已過的項目前端會自己隱藏；清單是空的就整段不顯示。

## 檔案格式

```json
{
  "updatedAt": "10/20 14:10",
  "publishedAt": "2026-10-20T06:10:23Z",
  "promos": [
    {
      "id": "nz-itf-2026",
      "airline": "紐西蘭航空",
      "title": "線上旅展",
      "discount": "58折起",
      "fromPrice": 29500,
      "taxIncluded": false,
      "bookFrom": "2026-10-20",
      "bookTo": "2026-11-09",
      "travelFrom": "2026-12-06",
      "travelTo": "2027-02-28",
      "routes": "台北－奧克蘭 AKL",
      "conditions": "一句話限制",
      "url": "https://www.airnewzealand.tw/flight-deals-to-new-zealand",
      "confirmed": true,
      "source": "https://www.airnewzealand.tw/flight-deals-to-new-zealand"
    }
  ]
}
```

- `updatedAt`：台北時間，`M/D HH:mm`（例如 `10/20 14:10`）。這是這份檔案的檢查時間，不驅動首頁「票價 N 小時前更新」（那個看 `deals.json` 的 `updatedAt`）。
- `publishedAt`：ISO UTC，例如 `2026-10-20T06:10:23Z`。
- `fromPrice`：新台幣數字，或 `null`（不知道起價就留空，卡片不寫價錢）。
- `taxIncluded`：一定要是 `true` 或 `false`。有起價時卡片會寫「含稅」或「未稅」。不確定時設 `false`，並在 `conditions` 寫明官網還沒說明稅費。
- `bookFrom` / `bookTo`：`YYYY-MM-DD`。沒有 `bookTo` 的項目不會顯示。
- `travelFrom` / `travelTo`：可飛日期，不知道就 `null`。
- `routes`：給人看的航點文字。票價卡上的「促銷中」會用這裡對目的地：寫了「全航線」就套到該航空所有航點；否則目的地中文（至少兩字）或三字代碼要出現在這段文字裡。航點還沒公告時不要寫「全航線」。
- `url`：必須是 `https://`。這是「看官網」按鈕。
- `confirmed`：只有官網頁面文字確實寫了折扣或日期才設 `true`。只見媒體預告、或官網還是舊活動／圖片裡才有的折扣，維持 `false`（卡片顯示灰色「未確認」，也不會在票價上加「促銷中」）。`source` 放你核對的那一頁。
- `airline` 用全名：紐西蘭航空、長榮航空、中華航空、星宇航空、國泰航空、新加坡航空。票價卡會再用簡稱（紐航、長榮、華航、星宇、國泰、新航）對上；酷航不會被當成新航。

## 每次怎麼更新

1. 打開下面的官網，對折扣、訂票期間、可飛日期、起價、稅費。
2. 過期（今天已晚於 `bookTo`）的項目刪掉。
3. 官網沒寫清楚的維持 `confirmed: false`，並在 `conditions` 寫你看到的頁面狀態。
4. 改 `updatedAt`（台北）和 `publishedAt`（UTC）。
5. 存檔後交給網站發布。靜態檔有一分鐘快取鍵，發布後重新打開「最新優惠」即可。

## 要查的頁面

- 紐西蘭航空：https://www.airnewzealand.tw/flight-deals-to-new-zealand
- 長榮航空：https://flights.evaair.com/zh-tw/online-travel-fair
- 中華航空：https://2026itf.china-airlines.com/ ，以及 china-airlines.com 的促銷頁
- 星宇航空：https://www.starlux-airlines.com/flights/zh-tw/flights-from-taiwan 與新聞室
- 台灣虎航：https://www.tigerairtw.com/ （這次沒有確認到進行中的旅展價，下次再查）
- 國泰航空：https://flights.cathaypacific.com/zh_TW/offers/ 與當年度旅展頁（2026 是 `online-travel-fair-2026-itf.html`，不要沿用已結束的 2025 頁）
- 新加坡航空：https://www.singaporeair.com/zh_TW/tw/plan-travel/local-promotions/tw-local-promotion/

新聞或社群可先用關鍵字「旅展」「折起」「促銷」找線索。找到之後仍要回到官網；沒有官網句子就不能設 `confirmed: true`。

## 2026-10-20 這次種子

| 航空 | 折扣 | confirmed | 原因 |
| --- | --- | --- | --- |
| 紐西蘭航空 | 58折起，NT$29,500 未稅 | true | 官網有促銷價、未含稅、促銷期至 2026/11/9，以及經濟艙最優價日期 |
| 長榮航空 | 全航線78折起 | false | 官網仍寫線上旅展已結束；78折是媒體預告 |
| 中華航空 | 76折起 | false | 官網有 10/16–11/21 購票抽獎期間，頁面文字沒有 76 折 |
| 星宇航空 | 85折起 | true | 2026/10/15 新聞稿與台灣出發航班頁，訂票至 11/23 |
| 國泰航空 | 8折起 | true | 2026 旅展頁：10/16–11/13 訂票，70+ 航點最優 8 折 |
| 新加坡航空 | 最高8折，泗水 NT$10,618 起含稅 | true | 台灣本地促銷頁，訂票至 11/12 |
