async (page) => {
  const tickers = ["0941", "0066", "0700", "12345"];
  const results = [];

  for (const ticker of tickers) {
    await page.getByRole("textbox", { name: "香港股票代號" }).fill(ticker);
    await page.getByTestId("stBaseButton-primaryFormSubmit").click();
    await page.waitForTimeout(22000);

    const text = await page.locator("body").innerText();
    const hasTraceback =
      text.includes("Traceback:") ||
      text.includes("NameError") ||
      text.includes("TypeError") ||
      text.includes("ModuleNotFoundError");
    const completed =
      text.includes("報告生成完成") ||
      text.includes("資料驗證未完成") ||
      text.includes("PDF報告已成功生成") ||
      text.includes("INVALID");

    results.push({
      ticker,
      completed,
      hasTraceback,
      hasTicker: text.includes(ticker) || text.includes(`${ticker}.HK`),
    });

    await page.reload();
    await page.waitForTimeout(3500);
  }

  return JSON.stringify(results, null, 2);
}
