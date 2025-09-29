from emodpy_malaria.weather import *
import os


def get_climate(
    tag="default",
    start_year="2019",
    start_day="001",
    end_year="2019",
    end_day="365",
    demo_fname="demographics.csv",
    fix_temp=None,
):
    # Specifications
    # Date Range
    start = "".join((start_year, start_day))
    end = "".join((end_year, end_day))

    # Demographics
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
    demo = os.path.join(ROOT_DIR, demo_fname)

    # Output folder to store climate files
    dir1 = "/".join(("inputs/climate", tag, "-".join((start, end))))

    if os.path.exists(dir1):
        print("Path already exists. Please check for existing climate files.")
        return
    else:
        print(
            "Generating climate files from {} for day {} of {} to day {} of {}".format(
                demo_fname, start_day, start_year, end_day, end_year
            )
        )
        os.makedirs(dir1)
        csv_file = os.path.join(dir1, "weather.csv")

        # Request Weather Files
        wa = WeatherArgs(
            site_file=demo,
            start_date=int(start),
            end_date=int(end),
            node_column="node_id",
            id_reference=tag,
        )
        wr: WeatherRequest = WeatherRequest(platform="Calculon")
        wr.generate(weather_args=wa, request_name=tag)
        wr.download(local_dir=dir1)

        print(f"Original files are downloaded in {dir1}")

        df, wa = weather_to_csv(weather_dir=dir1, csv_file=csv_file)
        df.to_csv(csv_file)


if __name__ == "__main__":
    get_climate(
        tag="Gridded world grump2.5arcmin",
        start_year="2019",
        end_year="2019",
        demo_fname="nodes.csv",
    )
