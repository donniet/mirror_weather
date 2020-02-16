import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, Gio, GdkPixbuf
import argparse
import requests

def get_weather(args):
    url = args.weather_url.format(args.lat, args.long)
    headers = {
        "User-Agent": "python/3.2 (Linux x86_64) requests/{} {}".format(requests.__version__, args.email),
        "Content-Type": "application/geo+json",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()["properties"]["periods"]

    print('error getting weather: {} {}'.format(response.status_code, response.text))
    return response.status_code    

class WeatherWindow(Gtk.Window):
    def __init__(self, args):
        Gtk.Window.__init__(self, title="weather")
        self.args = args

        self.grid = Gtk.Grid()
        
        self.titles = [Gtk.Label() for _ in range(args.items)]
        self.images = [Gtk.Image() for _ in range(args.items)]
        self.temp = [Gtk.Label() for _ in range(args.items)]

        for i in range(len(self.titles)):
            t = self.titles[i]
            p = self.temp[i]
            g = self.images[i]

            t.set_justify(Gtk.Justification.LEFT)
            p.set_justify(Gtk.Justification.CENTER)

            self.grid.attach(t, 0, 2*i, 2, 1)
            self.grid.attach(p, 0, 2*i+1, 1, 1)
            self.grid.attach(g, 1, 2*i+1, 1, 1)
            
            t.set_text("item {}".format(i))

        self.on_timeout(None)
        self.timeout_id = GLib.timeout_add_seconds(3600, self.on_timeout, None)

        self.add(self.grid)

    
    def on_timeout(self, user_data):
        weather = get_weather(self.args)

        if isinstance(weather, int):
            return True # try again later!

        for i in range(len(self.titles)):
            t = self.titles[i]
            p = self.temp[i]
            g = self.images[i]

            g.clear()

            if i > len(weather):
                t.set_text("not available")
                p.set_text("")
                continue

            icon = requests.get(weather[i]["icon"])
            if icon.status_code == 200:
                stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(icon.content))
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream)
                g.set_from_pixbuf(pixbuf)

            t.set_text(weather[i]["name"])
            p.set_text("{}°".format(weather[i]["temperature"]))

        return True

         

def main(args):
    get_styles()
    window = WeatherWindow(args)
    window.set_app_paintable(True)
    window.set_decorated(False)
    window.set_visual(window.get_screen().get_rgba_visual())
    window.connect("destroy", Gtk.main_quit)
    window.show_all()


    if not args.geometry is None:
        if not window.parse_geometry(args.geometry):
            print('geometry "{}" not parsed.')

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass

    print('shutting down')

def get_styles():
    css = b"""
    label { 
        font-size: 20px;
        font-family: Carlito; 
        color: white;
        text-shadow: grey;
    }
    GtkLayout {
       background-color: transparent;
    }

    /*
    GtkViewport {
        background-color: transparent;
    }
    */
    """

    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(css)

    context = Gtk.StyleContext()
    screen = Gdk.Screen.get_default()

    context.add_provider_for_screen(
        screen,
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--weather_url", help="url format to weather endpoint", default="https://api.weather.gov/points/{},{}/forecast")
    parser.add_argument("--email", help="email of user to send in user agent", default="me@me.com")
    parser.add_argument("--lat", help="lattitude", default=44.9270833)
    parser.add_argument("--long", help="longitude", default=-93.2081002)
    parser.add_argument("--items", type=int, help="number of forcast items to display", default=5)
    parser.add_argument("--geometry", help="window geometry")

    args = parser.parse_args()
    main(args)
