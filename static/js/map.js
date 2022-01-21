/*
* map.js
* A class that encapsulates the state of the index page map and
* provides methods for modifying the map
*/

'use strict';

export class HomepageMap {

    constructor() {
        this._map_type = '';
        this._markers = [];
        this._map = null;
        this._graphicsLayer = null;
    }

    // initialize a map with map_type 'gmap' or 'arcmap', takes a Dojo Deferred object
    initMap(map_type, deferred) {
        if (!['gmap', 'arcmap'].includes(map_type))
            throw new Error('Not a valid map type');

        document.getElementById('map').innerHTML = "";
        this._map_type = map_type;
        this._markers.length = 0;

        if (map_type === 'gmap')
            this._initGmap(deferred);
        else
            this._initArcmap(deferred);

    }

    // render pins on map with pop-up boxes corresponding to photos
    makeMarkers(pins, photos) {
        if (!['gmap', 'arcmap'].includes(this._map_type))
            throw new Error('Map not initialized');

        if (this._map_type === 'gmap')
            this._makeMarkersGmap(pins, photos);
        else
            this._makeMarkersArcmap(pins, photos);
    }

    // remove all pins from map
    clearMarkers() {
        // note: OK if map not initialized

        if (this._map_type === 'gmap')
            this._clearMarkersGmap();
        else if (this._map_type === 'arcmap')
            this._clearMarkersArcmap();
    }

    // helper function for initMap, specific to Google Maps
    _initGmap(deferred) {

        // The location of Princeton
        const directionsService = new google.maps.DirectionsService();
        const directionsRenderer = new google.maps.DirectionsRenderer();
        var princeton = { lat: 40.345539, lng: -74.657087 };
        var map = new google.maps.Map(document.getElementById("map"), {
            center: princeton,
            zoom: 16,
        });
        directionsRenderer.setMap(map);
        const onChangeHandler = function () {
            calculateAndDisplayRoute(directionsService, directionsRenderer);
        };

        const infoWindow = new google.maps.InfoWindow();
        const locationButton = document.createElement("button");
        locationButton.textContent = "Pan to Current Location";
        locationButton.classList.add("custom-map-control-button");
        map.controls[google.maps.ControlPosition.TOP_CENTER].push(locationButton);
        locationButton.addEventListener("click", () => {
            // Try HTML5 geolocation.
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const pos = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude,
                        };
                        infoWindow.setPosition(pos);
                        infoWindow.setContent("Location found.");
                        infoWindow.open(map);
                        map.setCenter(pos);
                    },
                    () => {
                        handleLocationError(true, infoWindow, map.getCenter());
                    }
                );
            } else {
                // Browser doesn't support Geolocation
                handleLocationError(false, infoWindow, map.getCenter());
            }
        });

        this._map = map;
        deferred.resolve("success");
    }

    // helper function for initMap, specific to ArcMaps
    _initArcmap(deferred) {

        require([
            "esri/Map",
            "esri/views/MapView",
            "esri/layers/GraphicsLayer",
            "esri/widgets/Locate",
            "esri/layers/TileLayer"
        ], (Map, MapView, GraphicsLayer, Locate, TileLayer) => {


            var map = new Map({

            });

            var layer = new TileLayer({
                url: ""
            });

            map.add(layer);

            var graphicsLayer = new GraphicsLayer();
            map.add(graphicsLayer);

            var view = new MapView({
                container: "map",
                map: map,
                center: [-74.657087, 40.345539], // longitude, latitude
                zoom: 8
            });

            view.constraints = {
                geometry: {            // Constrain lateral movement to Lower Manhattan
                    type: "extent",
                    xmin: -74.693232,
                    ymin: 40.302098,
                    xmax: -74.580678,
                    ymax: 40.371644
                },
                minZoom: 6
            };


            var locate = new Locate({
                view: view,
                useHeadingEnabled: false,
                goToOverride: function (view, options) {
                    options.target.scale = 1500;  // Override the default map scale
                    return view.goTo(options.target);
                }
            });

            view.ui.add(locate, "top-left");

            this._map = map;
            this._graphicsLayer = graphicsLayer;

            deferred.resolve("success");

        });
    }

    // helper function for makeMarkers, specific to Google Maps
    _makeMarkersGmap(pins, photos) {
        var photoNum = 0;
        var j = 0;
        for (var i = 0; i < pins.length; i += 5) {
            var images = []
            for (; j < photoNum + (2 * pins[i + 4]); j += 2) {
                var jsum = photoNum + (2 * pins[i + 4]);
                var image = {
                    type: "media",
                    title: photos[j + 1],
                    type: "image",
                    value: {
                        sourceURL: photos[j]
                    }
                }
                console.log(image.title)
                images.push(image)
            }
            photoNum = j;
            const latLng = new google.maps.LatLng(pins[i + 1], pins[i + 2])
            const marker = new google.maps.Marker({ position: latLng, map: this._map })
            this._markers.push(marker);

            var imageHTML = "";
            for (var im = 1; im < images.length; im++) {
                imageHTML += "<div class='carousel-item'>" + "<p style='text-align: center;'>" + images[im].title + "</p>" + "<img style='height: 25%; width: auto;' class='onMapPic' src='" + images[im].value.sourceURL + "' class='d-block w-100'></div>"
            }
            if (imageHTML == "") {
                var controls = ""
            } else {
                var controls = "<a class='carousel-control-prev' href='#carouselExampleControls' role='button' data-slide='prev'>" +
                    "<span class='carousel-control-prev-icon' aria-hidden='true'></span>" +
                    "<span class='sr-only'>Previous</span>" +
                    "</a>" +
                    "<a class='carousel-control-next' href='#carouselExampleControls' role='button' data-slide='next'>" +
                    "<span class='carousel-control-next-icon' aria-hidden='true'></span>" +
                    "<span class='sr-only'>Next</span>" +
                    "</a>"
            }
            const infowindow = new google.maps.InfoWindow({
                content: "<div><h2 style='text-align: center;'>" +
                    pins[i + 3] + "</h2>" +
                    "<div id='carouselExampleControls' class='carousel slide' data-ride='carousel'>" +
                    "<div class='carousel-inner'>" +
                    "<div class='carousel-item active'>" +
                    "<p style='text-align: center;'>" + images[0].title + "</p>" +
                    "<img style='height: 20%; width: auto;' class='onMapPic' src='" + images[0].value.sourceURL + "' class='d-block w-100'>" +
                    "</div>" +
                    imageHTML +
                    "</div>" +
                    controls +
                    "</div>" +
                    "<a style='display: flex; justify-content: center; color:black; background-color: coral; padding: 3px; font-size:25px' href='photo?pinid=" + pins[i] + "'>" +
                    "View Pin" +
                    "</a>" +
                    "</div>",
            });

            marker.addListener("click", () => {
                infowindow.open(this._map, marker);
            })
            this._map.addListener("click", () => {
                infowindow.close();
            })
        }
    }

    // helper function for makeMarkers, specific to ArcMap
    _makeMarkersArcmap(pins, photos) {
        require([
            "esri/Graphic"
        ], (Graphic) => {

            var simpleMarkerSymbol = {
                type: "simple-marker",
                color: [226, 119, 40], // orange
                outline: {
                    color: [255, 255, 255], // white
                    width: 1
                }
            };

            var photoNum = 0;
            var j = 0;
            for (var i = 0; i < pins.length; i += 5) {
                var point = {
                    type: "point",
                    longitude: pins[i + 2],
                    latitude: pins[i + 1]
                };

                var images = []

                for (; j < photoNum + (2 * pins[i + 4]); j += 2) {
                    var jsum = photoNum + (2 * pins[i + 4]);
                    var image = {
                        type: "media",
                        title: photos[j + 1],
                        type: "image",
                        value: {
                            sourceURL: photos[j]
                        }
                    }
                    images.push(image)
                }
                photoNum = j;

                // Create attributes
                var attributes = {
                    Name: pins[i + 3], // The name of the
                    // Location: " Point Dume State Beach" // The owner of the
                };
                // Create popup template
                var popupTemplate = {
                    title: "{Name}",
                    content: [{
                        type: "media",
                        mediaInfos:
                            images

                    },

                    {
                        type: "text",
                        text: "<hr><strong><p style='text-align: center;'><a target='_self' style='color:black; background-color: coral; padding: 3px; font-size:25px' href='"
                            + window.location.href.split('?')[0] + "photo?pinid=" + pins[i] + "'>View Pin</a></p></strong>"
                    }]
                };


                var pointGraphic = new Graphic({
                    geometry: point,
                    symbol: simpleMarkerSymbol,
                    attributes: attributes,
                    popupTemplate: popupTemplate
                });

                this._graphicsLayer.add(pointGraphic);
                this._markers.push(pointGraphic);
            }
        });
    }

    // helper function for clearMarkers, specific to Google Maps
    _clearMarkersGmap() {
        for (var i = 0; i < this._markers.length; i++) {
            this._markers[i].setMap(null);
        }
        this._markers.length = 0;
    }

    // helper function for clearMarkers, specific to ArcMap
    _clearMarkersArcmap() {
        for (var i = 0; i < this._markers.length; i++) {
            this._graphicsLayer.remove(this._markers[i]);
        }
        this._markers.length = 0;
    }
}