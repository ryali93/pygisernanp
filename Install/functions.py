import string

# Create a function that returns a list of letters
y = 0
with arcpy.da.UpdateCursor("gpo_grillas", ["letra", "numero", "x", "y"]) as cursor:
    for row in cursor:
        y_new = row[3]
        if abs(y - y_new) < 0.03:
            