from exceptions import SystemExit

import os
import sys
import traceback

FILENAME = 'fabfile-progress.txt'


def run_all_steps(steps, resume=False):
    """Run all fabric steps.

    @steps: a list of methods to run
    @resume: if True, continue from the last failed step. If False, start from
            the beginning
    """
    if not validate_steps(steps):
        print 'ERROR: Please provide a valid list of callables to run.'
        return
    try:
        start_index = resume and get_start_index(steps) or 0
        print 'Starting from step: %s' % steps[start_index].__name__
        for step in steps[start_index:]:
            step()
    except SystemExit:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        failed_step = traceback.extract_tb(exc_traceback)[1][2]
        save_progress(failed_step)
        print 'ERROR: Failed at step: %s' % failed_step
        return

    print 'All steps completed successfully.'
    delete_progress()


def validate_steps(steps):
    for step in steps:
        if not hasattr(step, '__call__'):
            return False
    return True


def save_progress(failed_step):
    """Save the last step that didn't complete successfully."""
    try:
        file = open(FILENAME, 'w')
        file.write(failed_step)
        file.close()
    except IOError:
        print 'ERROR: Failed to save progress. Resuming will not be possible.'


def delete_progress():
    try:
        os.remove(FILENAME)
    except OSError:
        pass


def get_start_index(steps):
    """Return the index of the last failed step.
    """
    if not os.path.isfile(FILENAME):
        return 0

    try:
        file = open(FILENAME, 'r')
        failed_step = file.readline().strip()
        step_names = [s.__name__ for s in steps]
        file.close()
        return step_names.index(failed_step)
    except (IOError, ValueError):
        print 'WARNING: Could not load the last step.'
        return 0
