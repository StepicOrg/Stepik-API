import argparse

from functions import get_drop_out_plot

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--course', type=int)
args = parser.parse_args()

if args.course:
    course_id = args.course

    # make a final plot
    get_drop_out_plot(course_id)
