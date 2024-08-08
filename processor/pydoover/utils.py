

## A function to map a reading to a value in a range
def map_reading(in_val, output_values, raw_readings=[4,20], ignore_below=3):

    if in_val < ignore_below:
        return None

    ## Choose the value set to map between
    lower_val_ind = 0
    found = False
    for i in range(0, len(raw_readings)):
        if in_val <= raw_readings[i]:
            lower_val_ind = i-1
            found = True
            break

    if not found:
        lower_val_ind = len(raw_readings)-2

    # Figure out how 'wide' each range is
    inSpan = raw_readings[lower_val_ind + 1] - raw_readings[lower_val_ind]
    outSpan = output_values[lower_val_ind + 1] - output_values[lower_val_ind]

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(in_val - raw_readings[lower_val_ind]) / float(inSpan)

    # Convert the 0-1 range into a value in the right range.
    return output_values[lower_val_ind] + (valueScaled * outSpan)
