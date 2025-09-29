import os
import pandas as pd
from emodpy_malaria.weather import *
from emodpy_malaria.weather.weather_variable import WeatherVariable
import manifest
import argparse


def parse_args():
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-generate_climate",
        action="store_true",
        help="Specify whether to generate new json and bin files off a custom weather csv",
    )
    parser.add_argument(
        "-generate_csv",
        action="store_true",
        help="Specify whether to generate csv based off of exisiting climate files",
    )
    parser.add_argument(
        "-climate_profile",
        type=str,
        required=False,
        default="generated_seasonal",
        help="Specify whether the custom pattern is perennial or seasonal in nature",
    )
    parser.add_argument(
        "-indir",
        type=str,
        required=False,
        default=os.path.join(manifest.emod_input_path),
        help="Specify the directory to find and then later store the new weather files",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    indir = args.indir
    df, wa = weather_to_csv(
        weather_dir=os.path.join(indir, "climate"), weather_file_prefix="seasonal"
    )

    # Create Climate CSV, which can be modified to create different .json and .bin files.
    if args.generate_csv:
        df1 = df.copy()
        df1["nodes"] = 1
        df1.to_csv(os.path.join(indir, f"{args.climate_profile}.csv"), index=False)

        # Create EMOD-readable weather files to be used in simulations from modified CSVs if needed
    if args.generate_climate:
        new_season_pattern = args.climate_profile
        df1 = pd.read_csv(
            os.path.join(indir, "generate_climate_files", f"{new_season_pattern}.csv")
        )

        weather_columns = {
            WeatherVariable.AIR_TEMPERATURE: "airtemp",
            WeatherVariable.RELATIVE_HUMIDITY: "humidity",
            WeatherVariable.RAINFALL: "rainfall",
            WeatherVariable.LAND_TEMPERATURE: "landtemp",
        }
        weather_filenames = {
            WeatherVariable.AIR_TEMPERATURE: f"{new_season_pattern}_air_temperature_daily.bin",
            WeatherVariable.RELATIVE_HUMIDITY: f"{new_season_pattern}_relative_humidity_daily.bin",
            WeatherVariable.RAINFALL: f"{new_season_pattern}_rainfall_daily.bin",
            WeatherVariable.LAND_TEMPERATURE: f"{new_season_pattern}_land_temperature_daily.bin",
        }

        csv_to_weather(
            df1,
            attributes=wa,
            weather_columns=weather_columns,
            weather_dir=os.path.join(indir, new_season_pattern),
            weather_file_names=weather_filenames,
        )
