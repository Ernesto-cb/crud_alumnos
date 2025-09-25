import requests
import os
import json  # Importamos json para formatear la salida
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.syntax import Syntax  # Para mostrar JSON formateado

# --- Configuración Inicial ---
console = Console()
BASE_URL = "http://127.0.0.1:5000"


# --- Funciones de Utilidad ---
def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')


def mostrar_banner():
    # (El banner se mantiene igual)
    banner = """
    Gestor de Estudiantes  
"""
    console.print(Panel(banner, style="bold cyan", border_style="cyan"))


def mostrar_estudiantes(estudiantes):
    # (La función para mostrar la tabla se mantiene igual)
    if not estudiantes:
        console.print("[yellow]No se encontraron estudiantes.[/yellow]")
        return
    tabla = Table(title="Lista de Estudiantes", border_style="magenta")
    tabla.add_column("No. Control", justify="right", style="cyan", no_wrap=True)
    tabla.add_column("Nombre", style="white")
    tabla.add_column("Apellido Paterno", style="white")
    tabla.add_column("Apellido Materno", style="white")
    tabla.add_column("Semestre", justify="right", style="green")
    for est in estudiantes:
        tabla.add_row(
            est.get('no_control', 'N/A'), est.get('nombre', 'N/A'),
            est.get('ap_paterno', 'N/A'), est.get('ap_materno', 'N/A'),
            str(est.get('semestre', 'N/A'))
        )
    console.print(tabla)


def mostrar_flujo_api(method, url, payload=None, response=None):
    """Muestra un panel con los detalles de la comunicación API."""
    info = f"[bold]Método:[/] [cyan]{method}[/]\n"
    info += f"[bold]URL:[/] [cyan]{url}[/]"

    if payload:
        # Formatear el JSON que se envía para que sea legible
        payload_str = json.dumps(payload, indent=2, ensure_ascii=False)
        info += "\n\n[bold]Payload Enviado:[/]"
        info += f"\n[green]{payload_str}[/green]"

    if response is not None:
        info += f"\n\n[bold]Respuesta del Servidor:[/]\n"
        info += f"[bold]Código de Estado:[/] [yellow]{response.status_code} {response.reason}[/yellow]"
        try:
            # Formatear el JSON recibido para que sea legible
            response_json = response.json()
            response_str = json.dumps(response_json, indent=2, ensure_ascii=False)
            info += "\n[bold]JSON Recibido:[/]"
            # Usamos el resaltador de sintaxis de rich para JSON
            syntax = Syntax(response_str, "json", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="[yellow]Detalles de la Conexión API[/yellow]", border_style="yellow"))
            return  # Salimos para no imprimir el panel dos veces
        except json.JSONDecodeError:
            info += f"\n[bold]Contenido Recibido (no es JSON):[/]\n{response.text}"

    console.print(Panel(info, title="[yellow]Detalles de la Conexión API[/yellow]", border_style="yellow"))


# --- Funciones de los Endpoints ---

def obtener_todos():
    """Obtiene y muestra todos los estudiantes del servidor."""
    url = f"{BASE_URL}/estudiantes"
    mostrar_flujo_api("GET", url)
    try:
        response = requests.get(url)
        mostrar_flujo_api("GET", url, response=response)
        response.raise_for_status()
        mostrar_estudiantes(response.json())
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error al conectar con el servidor:[/bold red] {e}")


def obtener_por_nocontrol():
    """Pide un número de control y muestra los datos del estudiante correspondiente."""
    no_control = Prompt.ask("[bold cyan]Introduce el Número de Control[/bold cyan]")
    url = f"{BASE_URL}/estudiantes/{no_control}"
    mostrar_flujo_api("GET", url)
    try:
        response = requests.get(url)
        mostrar_flujo_api("GET", url, response=response)
        if response.ok:
            mostrar_estudiantes([response.json()])
        else:
            console.print(f"[bold red]Respuesta no exitosa del servidor.[/bold red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error al conectar con el servidor:[/bold red] {e}")


def agregar_estudiante():
    """Pide los datos de un nuevo estudiante y lo envía al servidor."""
    console.print("\n[bold green]--- Agregar Nuevo Estudiante ---[/bold green]")
    estudiante_data = {
        "no_control": Prompt.ask("No. Control"),
        "nombre": Prompt.ask("Nombre(s)"),
        "ap_paterno": Prompt.ask("Apellido Paterno"),
        "ap_materno": Prompt.ask("Apellido Materno"),
        "semestre": IntPrompt.ask("Semestre")
    }
    url = f"{BASE_URL}/estudiantes"
    mostrar_flujo_api("POST", url, payload=estudiante_data)
    try:
        response = requests.post(url, json=estudiante_data)
        mostrar_flujo_api("POST", url, payload=estudiante_data, response=response)
        if response.status_code == 201:
            console.print(f"\n[bold green]Éxito:[/bold green] Estudiante agregado correctamente.")
        else:
            console.print(f"\n[bold red]Error al agregar estudiante.[/bold red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error al conectar con el servidor:[/bold red] {e}")


def actualizar_estudiante():
    """Pide el No. de Control y los nuevos datos para actualizar un estudiante."""
    no_control = Prompt.ask("[bold cyan]Introduce el No. de Control a actualizar[/bold cyan]")
    url = f"{BASE_URL}/estudiantes/{no_control}"
    # (Omitimos mostrar el flujo para la comprobación inicial para no ser redundantes)
    try:
        get_response = requests.get(url)
        if not get_response.ok:
            console.print(f"[bold red]Error:[/bold red] No se encontró al estudiante '{no_control}'.")
            mostrar_flujo_api("GET", url, response=get_response)
            return
        estudiante_actual = get_response.json()
        console.print("\n[bold]Datos actuales:[/bold]")
        mostrar_estudiantes([estudiante_actual])
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error al buscar estudiante:[/bold red] {e}")
        return

    console.print("\n[bold green]--- Nuevos Datos ---[/bold green] ([italic]deja en blanco para no cambiar[/italic])")
    update_data = {}

    # Pedir datos (este bloque es igual)
    nombre = Prompt.ask("Nombre", default=estudiante_actual.get('nombre'))
    if nombre != estudiante_actual.get('nombre'): update_data['nombre'] = nombre
    ap_paterno = Prompt.ask("Apellido Paterno", default=estudiante_actual.get('ap_paterno'))
    if ap_paterno != estudiante_actual.get('ap_paterno'): update_data['ap_paterno'] = ap_paterno
    ap_materno = Prompt.ask("Apellido Materno", default=estudiante_actual.get('ap_materno'))
    if ap_materno != estudiante_actual.get('ap_materno'): update_data['ap_materno'] = ap_materno
    semestre = IntPrompt.ask("Semestre", default=estudiante_actual.get('semestre'))
    if semestre != estudiante_actual.get('semestre'): update_data['semestre'] = semestre

    if not update_data:
        console.print("[yellow]No se realizó ningún cambio.[/yellow]")
        return

    mostrar_flujo_api("PATCH", url, payload=update_data)
    try:
        response = requests.patch(url, json=update_data)
        mostrar_flujo_api("PATCH", url, payload=update_data, response=response)
        if response.ok:
            console.print(f"\n[bold green]Éxito:[/bold green] Estudiante actualizado.")
        else:
            console.print(f"\n[bold red]Error al actualizar.[/bold red]")

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error al conectar con el servidor:[/bold red] {e}")


def eliminar_estudiante():
    """Pide el No. de Control y elimina al estudiante correspondiente."""
    no_control = Prompt.ask("[bold cyan]Introduce el No. de Control a eliminar[/bold cyan]")
    confirmacion = Prompt.ask(f"¿Seguro que deseas eliminar al estudiante '{no_control}'? (s/n)", default="n")

    if confirmacion.lower() != 's':
        console.print("[yellow]Operación cancelada.[/yellow]")
        return

    url = f"{BASE_URL}/estudiantes/{no_control}"
    mostrar_flujo_api("DELETE", url)
    try:
        response = requests.delete(url)
        mostrar_flujo_api("DELETE", url, response=response)
        if response.ok:
            console.print(f"\n[bold green]Éxito:[/bold green] Estudiante eliminado.")
        else:
            console.print(f"\n[bold red]Error al eliminar.[/bold red]")

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error al conectar con el servidor:[/bold red] {e}")


# --- Bucle Principal ---
def mostrar_menu():
    # (El menú se mantiene igual)
    menu = """
[bold]Menú Principal[/bold]
1. Ver todos los estudiantes
2. Buscar estudiante por No. de Control
3. Agregar un nuevo estudiante
4. Actualizar un estudiante
5. Eliminar un estudiante
6. Salir
"""
    console.print(Panel(menu, title="Opciones", border_style="green", expand=False))


def main():
    # (La función main se mantiene prácticamente igual)
    while True:
        limpiar_pantalla()
        mostrar_banner()
        mostrar_menu()

        opcion = IntPrompt.ask("[bold]Elige una opción[/bold]", choices=["1", "2", "3", "4", "5", "6"])

        limpiar_pantalla()
        mostrar_banner()

        if opcion == 1:
            console.print("\n[bold #50fa7b]--- LISTA DE TODOS LOS ESTUDIANTES ---[/bold #50fa7b]")
            obtener_todos()
        elif opcion == 2:
            console.print("\n[bold #50fa7b]--- BUSCAR ESTUDIANTE ---[/bold #50fa7b]")
            obtener_por_nocontrol()
        elif opcion == 3:
            agregar_estudiante()
        elif opcion == 4:
            console.print("\n[bold #50fa7b]--- ACTUALIZAR ESTUDIANTE ---[/bold #50fa7b]")
            actualizar_estudiante()
        elif opcion == 5:
            console.print("\n[bold #50fa7b]--- ELIMINAR ESTUDIANTE ---[/bold #50fa7b]")
            eliminar_estudiante()
        elif opcion == 6:
            console.print("[bold cyan]¡Hasta luego![/bold cyan] 👋")
            break

        Prompt.ask("\n[italic]Presiona Enter para continuar...[/italic]")


if __name__ == "__main__":
    main()