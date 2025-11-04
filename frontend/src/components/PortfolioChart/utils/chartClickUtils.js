// src/components/PortfolioChart/utils/chartClickUtils.js

export const handleChartClick = (e, data, onPointClick) => {
  if (!e) return;

  // // 🔹 kliknięcie bezpośrednio w punkt (np. aktywny payload)
  // if (e.activePayload && e.activePayload.length > 0) {
  //   onPointClick(e.activePayload[0].payload);
  //   return;
  // }

  // 🔹 kliknięcie w oś / puste miejsce — spróbuj znaleźć po dacie
  if (e.activeLabel && data) {
    const found = data.find((d) => d.date === e.activeLabel);
    if (found) onPointClick(found);
  }
};
