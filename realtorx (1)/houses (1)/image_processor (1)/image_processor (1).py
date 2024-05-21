from math import floor

from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO

default_user_logo_path = ""


class ImageProcessor:
    def __init__(self):
        self.logo_width = 170  # reduce calcs for now. this is width of logo realtorx/houses/user_default_logo.png
        self.padding = 0
        self.logo = Image.open("realtorx/houses/image_processor/user_default_logo.png")

    def _adjust_image_scale(self, image):
        width, height = image.size
        ratio = height / width

        if ratio < 1:
            new_width = floor(self.logo_width * 7)
            new_height = floor(ratio * new_width)
            new_image = image.resize((new_width, new_height), Image.ANTIALIAS)
            return new_image, new_width, new_height

        new_height = floor(self.logo_width * 7)
        new_width = floor(new_height / 1.5)
        new_image = image.resize((new_width, new_height), Image.ANTIALIAS)
        return new_image, new_width, new_height

    def _get_logo_position(self, new_width, new_height):
        return (
            new_width - self.logo_width - self.padding,
            new_height - self.logo_width - self.padding,
        )

    def add_logo(self, house):
        img_io = BytesIO()

        base_image = Image.open(house.main_photo)

        base_image, new_width, new_height = self._adjust_image_scale(base_image)

        logo_position = self._get_logo_position(new_width, new_height)

        base_image.paste(self.logo, logo_position, self.logo)

        base_image.save(img_io, format="JPEG", quality=90)
        img_content = ContentFile(img_io.getvalue(), "img.jpg")

        house.main_photo_with_avatar = img_content
        house.save()
        return house
