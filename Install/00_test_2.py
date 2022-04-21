import string
list_of_letters = [x+j for x in string.ascii_uppercase for j in string.ascii_uppercase]

y = 0
acumulador = 0
numero = 1
letra_ind = 0
with arcpy.da.UpdateCursor("gpo_grillas", ["letra", "numero", "x", "y"], None, sql_clause = (None, 'ORDER BY y DESC, x ASC')) as cursor:
    for row in cursor:
        if acumulador == 0:
            y = row[3]
        y_new = row[3]
        if abs(y - y_new) > 0.004:
            letra_ind = 0
            numero += 1
            y = row[3]
        letra = list_of_letters[letra_ind]
        acumulador += 1
        letra_ind += 1
        row[0] = letra
        row[1] = numero
        cursor.updateRow(row)


def asignar_codigos(anp_codi):
y = 0
acumulador = 0
numero = 1
letra_ind = 0
with arcpy.da.UpdateCursor("gpo_grillas", ["letra", "numero", "x", "y"], "anp_codi = '{}'".format(anp_codi), sql_clause = (None, 'ORDER BY y DESC, x ASC')) as cursor:
    for row in cursor:
        if acumulador == 0:
            y = row[3]
        y_new = row[3]
        if abs(y - y_new) > 0.004:
            letra_ind = 0
            numero += 1
            y = row[3]
        letra = list_of_letters[letra_ind]
        acumulador += 1
        letra_ind += 1
        row[0] = letra
        row[1] = numero
        cursor.updateRow(row)


import string
list_of_letters = [x+j for x in string.ascii_uppercase for j in string.ascii_uppercase]

y = 0
acumulador = 0
numero = 1
letra_ind = 0
with arcpy.da.UpdateCursor("gpo_grillas", ["letra", "numero", "x", "y"], None, 
                            sql_clause = (None, 'ORDER BY y DESC, x ASC')) as cursor:
    for row in cursor:
        if acumulador == 0:
            y = row[3]
        y_new = row[3]
        if abs(y - y_new) > 0.004:
            letra_ind = 0
            numero += 1
            y = row[3]
        letra = list_of_letters[letra_ind]
        acumulador += 1
        letra_ind += 1
        row[0] = letra
        row[1] = numero
        cursor.updateRow(row)



def asignar_codigos(anp_codi):
    import string
    list_of_letters = [x+j for x in string.ascii_uppercase for j in string.ascii_uppercase]

    y = 0
    acumulador = 0
    numero = 1
    letra_ind = 0
    with arcpy.da.UpdateCursor("gpo_grillas", ["letra", "numero", "x", "y"], "anp_codi = '{}'".format(anp_codi), sql_clause = (None, 'ORDER BY y DESC, x asc')) as cursor:
        for row in cursor:
            if acumulador == 0:
                y = row[3]
            y_new = row[3]
            if abs(y - y_new) > 200:
                letra_ind = 0
                numero += 1
                y = row[3]
            letra = list_of_letters[letra_ind]
            acumulador += 1
            letra_ind += 1
            row[0] = letra
            row[1] = numero
            cursor.updateRow(row)


with arcpy.da.UpdateCursor("grillas_anp", ["colu_char", "gma_colu"]) as cursorN:
    for x in cursorN:
        print(x)
        x[1] = dict_letteres[x[0]]
        cursorN.updateRow(x)