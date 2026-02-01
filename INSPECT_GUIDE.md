# How to Inspect Elements for Scraping 🕵️‍♂️

Mujhe scraper banane ke liye "Address" (Selectors) chahiye hote hain taaki code ko pata chale screen par kahan click karna hai aur kahan se text uthana hai.

Follow these simple steps:

## Step 1: Developer Tools Open Karein
1.  Apne Browser (Chrome/Edge) mein us page par jayein jahan data hai.
2.  Jis cheez ko scrape karna hai (jaise "Order ID" ya "Price"), us par **Right Click** karein.
3.  Menu mein sabse neeche **"Inspect"** par click karein.

## Step 2: Element ka Code Dekhein
Ek side panel khulega jisme colorful code hoga. Jo cheez aapne select ki thi, woh **Blue Highlighted** hogi.

Wahan aapko yeh cheezein dhundni hain:

### 1. ID (Sabse Best)
Agar code mein `id="LoginButton"` ya `id="table-row-1"` likha hai, toh yeh sabse best hai.
*   **Example**: `<button id="submit-btn" ... >`
*   **Mujhe Bhejein**: `id: #submit-btn`

### 2. Class (Common)
Zyadatar `class="..."` use hota hai.
*   **Example**: `<div class="invoice-amount total" ... >`
*   **Mujhe Bhejein**: `class: .invoice-amount` (Spaces ki jagah dot lagayein)

### 3. Parent Container (Bohat Zaroori)
Agar data ek Table ya List mein hai, toh mujhe **Row** ka code bhi chahiye.
*   Inspect panel mein thoda upar scroll karein jab tak pura row select na ho jaye (usually `<tr>` ya `<div class="card">`).
*   **Mujhe Bhejein**: "Har row ki class `.call-history-row` hai."

---

## Example Format (Mujhe aise data dein) 👇

**Page URL**: `https://portal.mongotel.com/invoices`

**1. Row/Container**:
> "Har invoice `<tr>` tag mein hai check karne par."

**2. Fields (Jo data chahiye)**:
> - **Invoice Date**: `params: class="date-col"`
> - **Amount**: `params: class="amount-text bold"`
> - **PDF Link**: `params: <a> tag hai jiske andar "Download" likha hai.`

**3. Next Button (Pagination)**:
> "Next page par jaane ke liye `id="pagination-next"` wala button hai."

---

### Shortcuts:
*   **Copy Selector**: Element par Right Click -> **Copy** -> **Copy selector**. (Yeh mujhe bhej dein, main safai kar lunga).
