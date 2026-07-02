def save_csv_for_excel(df, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        file.write("sep=;\n")
        df.to_csv(file, index=False, sep=";", decimal=",")
