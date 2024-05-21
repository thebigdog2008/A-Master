from imagekit import ImageSpec
from pilkit.processors import ResizeToFill, ResizeToFit, Transpose


class ThumbnailSpec(ImageSpec):
    processors = [
        Transpose(),
        ResizeToFit(width=720, upscale=False),
    ]
    format = "JPEG"
    options = {"quality": 100}


class SquareThumbnailSpec(ImageSpec):
    processors = [
        Transpose(),
        ResizeToFill(width=450, height=450),
    ]
    format = "JPEG"
    options = {"quality": 100}
