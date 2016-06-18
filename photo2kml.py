import sys
import glob
import simplekml
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def get_exif_data(image):
    """
    Returns a dictionary from the exif data of an PIL Image item.
    Also converts the GPS Tags
    https://gist.github.com/valgur/2fbed04680864fab1bfc
    """

    info = image._getexif()
    if not info:
        return {}
    exif_data = {TAGS.get(tag, tag): value for tag, value in info.items()}

    def is_fraction(val):
        return isinstance(val, tuple) and len(val) == 2 and isinstance(
            val[0], int) and isinstance(val[1], int)

    def frac_to_dec(frac):
        return float(frac[0]) / float(frac[1])

    if 'GPSInfo' in exif_data:
        gpsinfo = {GPSTAGS.get(t, t): v
                   for t, v in exif_data['GPSInfo'].items()}
        for tag, value in gpsinfo.items():
            if is_fraction(value):
                gpsinfo[tag] = frac_to_dec(value)
            elif all(is_fraction(x) for x in value):
                gpsinfo[tag] = tuple(map(frac_to_dec, value))
        exif_data['GPSInfo'] = gpsinfo

    return exif_data


def get_lat_lon(exif_data):
    """
    Returns the latitude and longitude (if available) from exif_data.
    https://gist.github.com/valgur/2fbed04680864fab1bfc
    """
    lat = None
    lon = None
    gps_info = exif_data.get('GPSInfo')

    def convert_to_degrees(value):
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)

    if gps_info:
        gps_latitude = gps_info.get('GPSLatitude')
        gps_latitude_ref = gps_info.get('GPSLatitudeRef')
        gps_longitude = gps_info.get('GPSLongitude')
        gps_longitude_ref = gps_info.get('GPSLongitudeRef')

        if (gps_latitude and gps_latitude_ref and gps_longitude and
                gps_longitude_ref):
            lat = convert_to_degrees(gps_latitude)
            if gps_latitude_ref == 'S':
                lat = -lat

            lon = convert_to_degrees(gps_longitude)
            if gps_longitude_ref == 'W':
                lon = -lon

    return lat, lon


def export_kml_file(file_names, kml_name):
    """
    Creates the kml document
  """
    kml = simplekml.Kml()

    for file_name in file_names:

        print('Reading ' + file_name + '...')

        with Image.open(file_name) as image:
            exif_data = get_exif_data(image)

        lat, lon = get_lat_lon(exif_data)

        pnt = kml.newpoint(name=file_name)
        pnt.coords = [(lon, lat)]

        # Add comtent to popup window
        pnt.description = (
            '<![CDATA[ <img src=' + file_name + ' height="500px" />]]>')
        pnt.stylemap.normalstyle.iconstyle.scale = 1
        pnt.stylemap.normalstyle.iconstyle.icon.href = (
            'http://maps.google.com/'
            'mapfiles/kml/shapes/camera.png')
        pnt.stylemap.highlightstyle.iconstyle.scale = 2
        pnt.stylemap.highlightstyle.iconstyle.icon.href = file_name

    kml.save(kml_name)


def main():

    if len(sys.argv) == 1:
        file_names = glob.glob('*.jpg')
    else:
        file_names = glob.glob(sys.argv[1])
    export_kml_file(file_names, 'output.kml')


if __name__ == '__main__':
    main()
