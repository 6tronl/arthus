import pandas as pd
import fiftyone as fo
import fiftyone.utils.data as foud
import geopandas
import os
from artus.spatialize.GeoCOCOExporter import GeoCOCOExporter

class FiftyoneGeoExporter(foud.LabeledImageDatasetExporter, GeoCOCOExporter): 
    """Export a fiftyone dataset to a geospatial format (geojson).

     Datasets of this type are exported in the following format:

         <export_dir>/
             dest_name.geojson

     where ``dest_name.geojson`` is a GeoJson file containing labels.
    
     Args:
         export_dir: the directory to write the export
         label_type : the label_type of the concerned fiftyone field ('polylines' for segmentation annotations or 'detections' for bbox annotations)
         epsg_code : the epsg code (for example : '4326' for world coordinates) in which the results will be exported
         dest_name : the file name of the geojson file with the extension (for example : 'spatial_predictions.geojson')
    """

    def __init__(self, export_dir, label_type, epsg_code, dest_name):
        super().__init__(export_dir=export_dir)
        self._data_dir = None
        self._labels_path = None
        self._labels = None
        self._image_exporter = None
        self.label_type = label_type
        self.epsg_code = epsg_code
        self.dest_name = dest_name
        self.sample_dir = None

    @property
    def requires_image_metadata(self):
        """Whether this exporter requires
         :class:`fiftyone.core.metadata.ImageMetadata` instances for each sample
         being exported.
        """
        return True

    @property
    def label_cls(self):
        """The :class:`fiftyone.core.labels.Label` class(es) exported by this
         exporter.

         This can be any of the following:

         -   a :class:`fiftyone.core.labels.Label` class. In this case, the
             exporter directly exports labels of this type
         -   a list or tuple of :class:`fiftyone.core.labels.Label` classes. In
             this case, the exporter can export a single label field of any of
             these types
         -   a dict mapping keys to :class:`fiftyone.core.labels.Label` classes.
             In this case, the exporter can handle label dictionaries with
             value-types specified by this dictionary. Not all keys need be
             present in the exported label dicts
         -   ``None``. In this case, the exporter makes no guarantees about the
             labels that it can export
        """
        return [fo.Detections, fo.Polylines]

    def setup(self):
        """Performs any necessary setup before exporting the first sample in
         the dataset.

         This method is called when the exporter's context manager interface is
         entered, :func:`DatasetExporter.__enter__`.
        """
        self._labels_path = os.path.join(self.export_dir, self.dest_name)
        self._labels = []

        self.columns_names = ['img_filename', 'label' ,'confidence', 'geometry']
        
        self._image_exporter = foud.ImageExporter(
            False, export_path=self._data_dir, default_ext=".jpg",
        )
        self._image_exporter.setup()

    def log_collection(self, sample_collection):
        self.sample_collection = sample_collection

    def shapely_polygons(self, label, metadata):
        imw, imh = (metadata.width, metadata.height)
        if self.label_type=='detections':
            polygon = label.to_shapely(frame_size=(imw,imh))
        elif self.label_type=='polylines':
            polygon = label.to_shapely(frame_size=(imw,imh))
        return polygon

    def export_sample(self, image_or_path, label, metadata=None):
        """Exports the given sample to the dataset.

        Args:
            image_or_path: an image or the path to the image on disk
            label: an instance of :meth:`label_cls`, or a dictionary mapping
                 field names to :class:`fiftyone.core.labels.Label` instances,
                 or ``None`` if the sample is unlabeled
            metadata (None): a :class:`fiftyone.core.metadata.ImageMetadata`
                 instance for the sample. Only required when
                 :meth:`requires_image_metadata` is ``True``
        """

        sample = self.sample_collection[image_or_path]
        metadata = sample.metadata

        # Get field values
        for n_label in getattr(label, self.label_type):

            img_filename = sample.filepath
            label = n_label.label
            confidence = n_label.confidence
            geometry = self.shapely_polygons(n_label, metadata)                

            gdf_row = (img_filename , label , confidence, geometry)

            self._labels.append(gdf_row)
        
        
    def close(self, *args):
        """Performs any necessary actions after the last sample has been
        exported.
        This method is called when the exporter's context manager interface is
        exited, :func:`DatasetExporter.__exit__`.

        Args:
            *args: the arguments to :func:`DatasetExporter.__exit__`
        """
        
        # Ensure the base output directory exists
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
            
        #convert _labels into gdf
        df = pd.DataFrame(data=self._labels, columns=self.columns_names)
        gdf = geopandas.GeoDataFrame(df, geometry='geometry')

        #convert pixel-values coordinates into geospatial coordinates
        gdf['transform'] =  [self.get_transform(sample) for sample in gdf['img_filename']]
        affine_transformed_gdf = self.affine_transform(gdf)
        affine_transformed_gdf = affine_transformed_gdf.filter(items=['img_filename', 'label', 'confidence', 'geometry'])
        affine_transformed_gdf.to_file(os.path.join(self.export_dir, self.dest_name), driver='GeoJSON')