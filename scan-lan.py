import pyvisa

# Crear el recurso de VISA
rm = pyvisa.ResourceManager("@py")

# Buscar los dispositivos disponibles
dispositivos = rm.list_resources('?*INSTR')

# Mostrar los dispositivos encontrados
print("Dispositivos encontrados en la red:")
for dispositivo in dispositivos:
    print(dispositivo)
