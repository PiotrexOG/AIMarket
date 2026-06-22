def save_csv_for_excel(df, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        file.write("sep=;\n")
        df.to_csv(file, index=False, sep=";", decimal=",")


def clean_outputs(output_dir):
    for csv_file in output_dir.glob("*.csv"):
        try:
            csv_file.unlink()
        except PermissionError:
            print(f"[SKIP] Could not delete open file: {csv_file}")

    for plot_file in output_dir.rglob("*.png"):
        try:
            plot_file.unlink()
        except PermissionError:
            print(f"[SKIP] Could not delete open file: {plot_file}")
