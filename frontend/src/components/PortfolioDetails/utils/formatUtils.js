// src/components/PortfolioDetails/utils/formatUtils.js
export const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);

  const formattedDate = date.toLocaleDateString("en-CA");
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  const formattedTime = `${hours}:${minutes}`;
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  return { date: formattedDate, time: formattedTime, timeZone };
};
