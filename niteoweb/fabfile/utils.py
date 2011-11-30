import os
import sys
import traceback

FILENAME = 'fabfile-progress.txt'


def run_all_steps(steps, resume=True, start_step=None):
    """Run all fabric steps.

    @steps: a list of methods to run
    @resume: if True, continue from the last failed step or from the provided
             start_step. If False, start from the beginning.
    @start_step: resume from this step
    """

    if not validate_steps(steps):
        print 'ERROR: Please provide a valid list of callables to run.'
        return

    start_index = resume and get_start_index(steps, start_step) or 0
    print 'Starting from step: %s' % steps[start_index].__name__

    for step in steps[start_index:]:
        try:
            step()
        except Exception:
            save_progress(step.__name__)
            print 'ERROR: Failed at step: %s\n' % step.__name__
            traceback.print_exc()
            return

    print 'All steps completed successfully.'
    delete_progress()


def validate_steps(steps):
    """Basic validation of the steps to see if they're callable."""
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
    """Delete saved progress."""
    try:
        os.remove(FILENAME)
    except OSError:
        pass


def get_start_index(steps, start_step):
    """Return the index of the starting step."""
    if start_step:
        try:
            start_index = get_step_index(steps, start_step)
        except ValueError:
            print "ERROR: Please enter a valid start step."
            sys.exit(1)
    elif not os.path.isfile(FILENAME):
        start_index = 0
    else:
        try:
            file = open(FILENAME, 'r')
            failed_step = file.readline().strip()
            file.close()
            start_index = get_step_index(steps, failed_step)
        except (IOError, ValueError) as e:
            print 'WARNING: Failed to load the last step. Starting from ' \
                  'the beginning..'
            start_index = 0

    return start_index


def get_step_index(steps, step_name):
    """Get step index for the provided step name."""
    step_names = [s.__name__ for s in steps]

    return step_names.index(step_name)
