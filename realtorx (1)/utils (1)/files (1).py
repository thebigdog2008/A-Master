import os
import uuid


def get_random_filename(instance, filename):
    extension = os.path.splitext(filename)[1]
    return "media/{uuid1}/{uuid2}{extension}".format(
        uuid1=uuid.uuid4(), uuid2=uuid.uuid4(), extension=extension
    )


def get_random_videoname(instance, filename):
    extension = os.path.splitext(filename)[1]
    return "media/videos/houses/{uuid1}/{uuid2}{extension}".format(
        uuid1=uuid.uuid4(), uuid2=uuid.uuid4(), extension=extension
    )


def get_random_video_thumbname(instance, filename):
    extension = os.path.splitext(filename)[1]
    return "media/videos/houses/thumbnails/{uuid1}/{uuid2}{extension}".format(
        uuid1=uuid.uuid4(), uuid2=uuid.uuid4(), extension=extension
    )


def get_document_path(instance, filename):
    return "documents/{uuid}/{filename}".format(uuid=uuid.uuid4(), filename=filename)


def get_agency_logo_path(instance, filename):
    return "agencylogo/{uuid}/{filename}".format(uuid=uuid.uuid4(), filename=filename)


def get_random_feedback_file(instance, filename):
    return "feedback/{uuid}/{filename}".format(uuid=uuid.uuid4(), filename=filename)


def get_random_home_video_file(instance, filename):
    return "homescreen/{uuid}/{filename}".format(uuid=uuid.uuid4(), filename=filename)
