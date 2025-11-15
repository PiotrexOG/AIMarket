export const groupTransactionsByNearestPoint = (
  transactions,
  chartData
) => {
  const groupedByDate = {};

  transactions.forEach((t) => {
    const transactionDate = new Date(t.datetime);

    const matchingPoint = chartData.reduce((prev, curr) => {
      const prevDiff = Math.abs(new Date(prev.date) - transactionDate);
      const currDiff = Math.abs(new Date(curr.date) - transactionDate);
      return currDiff < prevDiff ? curr : prev;
    });

    const key = matchingPoint.date;

    if (!groupedByDate[key]) groupedByDate[key] = [];
    groupedByDate[key].push(t);
  });

  return Object.entries(groupedByDate).map(([date, txs]) => {
    const avgRatio = txs.reduce((sum, t) => sum + t.ratio, 0) / txs.length;
    const matchingPoint = chartData.find((p) => p.date === date);

    const isPositive = avgRatio > 0;
    const scale = Math.min(Math.abs(avgRatio), 1);
    const size = 8 + scale * 10;

    return {
      x: date,
      y: matchingPoint.value,
      isUp: isPositive,
      size,
      avgRatio,
      originalTransactions: txs,
    };
  });
};
