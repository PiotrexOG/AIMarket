export const generateDistinctColors = (count) => {
  const colors = [];
  const saturation = 70; // Wysoka saturacja - żywe kolory
  const lightness = 60;  // Średnia jasność - dobra czytelność
  
  for (let i = 0; i < count; i++) {
    // Użycie złotego podziału do równomiernego rozłożenia kolorów w spektrum
    const hue = (i * 137.508) % 360; // Złoty kąt - zapewnia maksymalną różnorodność
    colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
  }
  
  return colors;
};