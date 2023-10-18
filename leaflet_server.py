import io
from pathlib import Path

import numpy as np

from astropy import units as u
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy import table

from PIL import Image, ImageDraw

import flask

TILE_SIZE = 10000
TILE_ISCALE = 13688.212927755822


app = flask.Flask(__name__)

data_path = Path('../deep_coadd_images')
tilings = table.Table.read('../ic1512_tilings.csv')
tilings_map = {(row['X'], row['Y']): row['FNSTEM'] for row in tilings}

@app.route('/')
def index():
    return get_viewer_str('image', 1024)

@app.route('/test')
def test():
    return get_viewer_str('test')


def get_viewer_str(imagetype, heightpx=600):
    return """
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.4.0/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.4.0/dist/leaflet.js"></script>
    <style>
        #map{ height: <HEIGHTPX>px;}
    </style>
    <div id="map"></div>

    <script>


    var map = L.map('map', {crs: L.CRS.Simple}).setView([0, 0], 11);

    map.redrawint = Math.floor( Math.random() * 200000 ) + 1
    var getRedrawInteger = function() {
        return map.redrawint;
    };

    var tilelayer = L.tileLayer('/<IMAGETYPE>{cachebuster}/{z}/{x}/{y}.png', {
        attribution: 'fitsfile', minZoom: 1, maxZoom:18, noWrap: true,
        tileSize:<TILESIZE>,
        maxNativeZoom: 1,
        minNativeZoom: 1,
        keepBuffer: 1,
        cachebuster: getRedrawInteger
    }).addTo(map);

    var bounds = [[-1,-1], [1,.5]];
    var image = L.imageOverlay('/test413241234/666/1000/1000.png', bounds).addTo(map);

    </script>
    """.replace('<HEIGHTPX>', str(heightpx)).replace('<IMAGETYPE>', imagetype).replace('<TILESIZE>', '1.005')



@app.route('/image<int:cachebuster>/<string:z>/<string:a>/<string:b>.png')
def get_subimage(z, a, b, cachebuster):
    x = int(a)
    y = -int(b)

    tilefn = tilings_map.get((x, y), None)
    print(x,y, tilefn)
    
    # sc = SkyCoord(float(x)*u.deg, float(y)*u.deg)
    # seps = sc.separation(cached_corners[data_path])
    # closest_basename = list(cached_corner_to_png[data_path].values())[np.argmin(seps)]
    # print('arg',z,x,y, closest_basename)

    if tilefn is None:
        flask.abort(404)
    else:
        return flask.send_file(data_path / (tilefn + '.png'), mimetype='image/png')



@app.route('/test<int:cachebuster>/<string:z>/<string:a>/<string:b>.png')
def test_image(z, a, b, cachebuster):
    x = int(a)
    y = -int(b)
    print('test',z,x,y)

    im = Image.new('L', (256, 256), 2**8)
    d = ImageDraw.Draw(im)
    d.text((128, 128), f'{x},{y},{z}', font_size=50, anchor='mm')

    with io.BytesIO() as output:
        im.save(output, format="png")
        return output.getvalue()


if __name__ == '__main__':
    app.run(debug=True)


# fuzzy thing at {lat: -0.414031982421875, lng: -0.076385498046875} - 22 02 32.69 -51 37 02.2


"""
var bounds = [[0,0], [1000,1000]];
var image = L.imageOverlay('uqm_map_full.png', bounds).addTo(map);
"""