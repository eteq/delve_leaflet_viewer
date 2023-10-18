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

app = flask.Flask(__name__)

data_path = Path('../deep_coadd_images/')

def make_tiledicts(inpath):
    tile_to_png = {p.stem:p for p in inpath.glob('*.png')}
    tiles_to_hdr = {k:p.with_suffix('.hdr1') for k,p in tile_to_png.items()}
    return tile_to_png, tiles_to_hdr
tilenm_to_png, tilenm_to_hdr = make_tiledicts(data_path)


@app.route('/')
def index(heightpx=600):
    return """
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.5.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.5.1/dist/leaflet.js"></script>
    <link rel="stylesheet" href="/static/Control.Coordinates.css" />
    <script src="/static/Control.Coordinates.js"></script>
    
    <style>
        #map{ height: <HEIGHTPX>px;}
        #image_idx { width: 5em;}
    </style>
    <div id="image controls">
        <button onclick="imagePrev()"> < </button>
        <input type="text" onChange=idxChanged() id="image_idx" value="0"> / <span id="image_count">-1</span> 
        <button onclick="imageNext()"> > </button>
        : <span id="image_name">NONE</span>
    </div>
    <div id="map"></div>

    <script>

    var currentImage = null;
    var preloadedImage =  new Image();

    function imageNext() {
        idx_elem = document.getElementById("image_idx");
        newidx = parseInt(idx_elem.value) + 1;
        load_image(tile_names[newidx]);
        idx_elem.value = newidx;
        
        preloadedImage.src = '/tile/' + tile_names[newidx+1];
    }

    function imagePrev() {
        idx_elem = document.getElementById("image_idx");
        newidx = parseInt(idx_elem.value) - 1;
        load_image(tile_names[newidx]);
        idx_elem.value = newidx;

        preloadedImage.src = '/tile/' + tile_names[newidx-1];
    }

    function idxChanged() {
        idx_elem = document.getElementById("image_idx");
        load_image(tile_names[parseInt(idx_elem.value)]);
    }

    function load_image(tilename) {
        document.getElementById('image_name').innerHTML = "Loading...";

        fetch('/header/' + tilename)
        .then(response => response.json())
        .then(hdr => {
            racs = [hdr.RAC1, hdr.RAC2, hdr.RAC3, hdr.RAC4];
            deccs = [hdr.DECC1, hdr.DECC2, hdr.DECC3, hdr.DECC4];
            maxra = Math.max(...racs);
            minra = Math.min(...racs);
            maxdec = Math.max(...deccs);
            mindec = Math.min(...deccs);

            //bounds = [[minra, mindec], [maxra, maxdec]];
            bounds = [[mindec, minra], [maxdec, maxra]];

            if (currentImage != null) {
                map.removeLayer(currentImage);
            }
            
            currentImage = L.imageOverlay('/tile/' + tilename, bounds).addTo(map);

            document.getElementById('image_name').innerHTML = tilename;

            //map.panTo([hdr.RA_CENT, hdr.DEC_CENT]);
            map.panTo([hdr.DEC_CENT, hdr.RA_CENT]);

            });
    }

    //var map = L.map('map', {crs: L.CRS.Simple}).setView([0, 0], 8);
    var map = L.map('map').setView([0, 0], 10);

    var c = new L.Control.Coordinates();
    c.addTo(map);

    map.on('click', function(e) {
        c.setCoordinates(e);
    });


    fetch('/tilelist')
    .then(response => response.json())
    .then(data => {
        tile_names = data;
        document.getElementById('image_count').innerHTML = tile_names.length;
    });

    </script>
    """.replace('<HEIGHTPX>', str(heightpx))


@app.route('/tile/<string:tilename>')
def get_tile_png(tilename):
    if tilename not in tilenm_to_png:
        return flask.Response(status=404)
    
    return flask.send_file(tilenm_to_png[tilename], mimetype='image/png')


@app.route('/header/<string:tilename>')
def get_tile_header(tilename):
    if tilename not in tilenm_to_hdr:
        return flask.Response(status=404)
    
    h = fits.Header.fromfile(tilenm_to_hdr[tilename])
    return flask.jsonify({k:str(v) for k,v in h.items()})


@app.route('/tilelist')
def get_tilelist():
    return flask.jsonify(list(tilenm_to_png.keys()))


if __name__ == '__main__':
    app.run(debug=True)