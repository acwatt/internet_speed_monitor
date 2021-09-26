import os
import logging
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import dates, rcParams
import time

SPEEDTEST_CMD = '/home/a/anaconda3/envs/internet_speed_monitor/bin/speedtest-cli'
ROOT = Path('/media/a/E/Programming/github/internet_speed_monitor')
LOG_FILE = (ROOT / 'speedtest.log').as_posix()


def main(number_pings, sleep_mins):
    config_logging()
    time.sleep(10)  # sometimes the first call results in no network connection
    while True:
        for ping_counter in range(number_pings):  # Ping the server 30 times
            print(f'\rPinging: {ping_counter} of {number_pings}            ', end='')
            try:
                ping, download, upload = get_ping_results()
                logging.info("%5.2f %5.2f %5.2f", ping, download, upload)
            except ValueError as err:
                logging.info(err)
        # update the plot after every pinging session
        create_plot(read_data())
        for minute in range(sleep_mins):
            print(f'\rSleeping: {minute+1} of {sleep_mins} minutes', end='')
            time.sleep(60)


def config_logging():
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M", )


def get_ping_results():
    ping = download = upload = None

    with os.popen(SPEEDTEST_CMD + ' --simple') as speedtest_output:
        for line in speedtest_output:
            label, value, unit = line.split()
            if 'Ping' in label:
                ping = float(value)
            elif 'Download' in label:
                download = float(value)
            elif 'Upload' in label:
                upload = float(value)

    if all((ping, download, upload)):
        return ping, download, upload
    else:
        raise ValueError('TEST FAILED')


def read_data():
    dataframe = pd.io.parsers.read_csv(LOG_FILE, names='date time ping download upload'.split(),
                                       header=None, sep=r'\s+', parse_dates={'timestamp': [0, 1]},
                                       na_values=['TEST', 'FAILED'], )
    csv_path = (ROOT / 'speedtest_data.csv')
    dataframe.to_csv(csv_path)
    return dataframe


def create_plot(df):
    rcParams['xtick.labelsize'] = 'xx-small'

    minute = df.groupby(df['timestamp'].dt.floor('Min')).mean().reset_index()
    hour = df.groupby(df['timestamp'].dt.floor('H')).mean().reset_index()

    plot_speed(minute, 'minute')
    plot_speed(hour, 'hour')


def plot_speed(df, frequency):
    plot_file_name = (ROOT / f'bandwidth_by-{frequency}.png').as_posix()

    plt.plot(df['timestamp'], df['download'], 'b-', label='download')
    plt.plot(df['timestamp'], df['upload'], 'r-', label='upload')
    plt.title(f'Jungle Ethernet Internet Speed (avg by {frequency})')
    plt.ylabel('Bandwidth in MBps')

    plt.xlabel('Date/Time')
    plt.xticks(rotation='45')

    plt.grid()
    plt.legend()

    current_axes = plt.gca()
    current_figure = plt.gcf()

    hfmt = dates.DateFormatter('%m/%d %H:%M')
    current_axes.xaxis.set_major_formatter(hfmt)
    current_figure.subplots_adjust(bottom=.25)

    loc = current_axes.xaxis.get_major_locator()
    loc.maxticks[dates.HOURLY] = 24
    loc.maxticks[dates.MINUTELY] = 20

    current_figure.savefig(plot_file_name)
    plt.close()
    # current_figure.show()


if __name__ == '__main__':
    # main() should be running at all times
    # comment out main() to just plot
    main(number_pings=20, sleep_mins=5)

