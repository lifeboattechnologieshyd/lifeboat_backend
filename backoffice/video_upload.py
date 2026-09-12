# views.py

import os
import uuid

from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from db.models import Video
from shared.clients.aws.s3 import get_s3_client, get_media_convert_client
from shared.utils import CustomResponse

class Videos(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        videos = Video.objects.all()
        res = []
        #todo : course needs to be onetoone realtion not char field
        for item in videos:
            res.append(
                {
                    "video_id": item.id,
                    "name": item.name,
                    "original_key": item.original_key,
                    "hls_key": item.hls_key,
                    "status": item.status,
                    "language": item.language,
                    "course_id": item.course_id,
                }
            )
        return CustomResponse.successResponse(data=res)


class VideoUploadURLAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        filename = request.data.get("filename")
        content_type = request.data.get("content_type")
        course_id = request.data.get("course_id")
        language = request.data.get("language")
        if not course_id:
            return CustomResponse.errorResponse(
                description="Course ID is required"
            )
        if not language:
            return CustomResponse.errorResponse(
                description="Language is required"
            )
        if not filename:
            return CustomResponse.errorResponse(
                description="Filename is required"
            )
        if not content_type:
            return CustomResponse.errorResponse(
                description="Content type is required"
            )
        if content_type != "video/mp4":
            return CustomResponse.errorResponse(
                description="Only MP4 videos are allowed"
            )
        extension = os.path.splitext(filename)[1].lower()
        if extension != ".mp4":
            return CustomResponse.errorResponse(
                description="Only MP4 videos are allowed"
            )
        video_id = uuid.uuid4()
        safe_filename = os.path.basename(filename)
        s3_key = (
            f"originals/courses/"
            f"{course_id}/"
            f"{language}/"
            f"{video_id}/{safe_filename}"
        )
        try:
            s3 = get_s3_client()
            upload_url = s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.AWS_VIDEO_BUCKET_NAME,
                    "Key": s3_key,
                    "ContentType": content_type,
                },
                ExpiresIn=900,
            )
            video = Video.objects.create(
                id=video_id,
                name=safe_filename,
                course_id=course_id,
                language=language,
                original_key=s3_key,
                status="uploaded",
            )
            return CustomResponse.successResponse(
                data={
                    "video_id": str(video.id),
                    "upload_url": upload_url,
                    "original_key": s3_key,
                }
            )

        except Exception as e:
            return CustomResponse.errorResponse(
                description=str(e)
            )


class VideoConvertAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            video_id = data.get("video_id", "")
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return CustomResponse.errorResponse(
                description="Video not found"
            )

        # Prevent duplicate MediaConvert jobs
        if video.status == "processing":
            return CustomResponse.errorResponse(
                description="Video is already being processed"
            )

        if video.status == "ready":
            return CustomResponse.errorResponse(
                description="Video is already converted"
            )

        if not video.original_key:
            return CustomResponse.errorResponse(
                description="Original video is missing"
            )

        try:
            mediaconvert = get_media_convert_client()
            input_s3 = (
                f"s3://{settings.AWS_VIDEO_BUCKET_NAME}/"
                f"{video.original_key}"
            )

            output_prefix = (
                f"s3://{settings.AWS_VIDEO_BUCKET_NAME}/"
                f"hls/courses/"
                f"{video.course_id}/"
                f"{video.language}/"
                f"{video.id}/"
            )

            job = mediaconvert.create_job(
                Role=settings.AWS_MEDIACONVERT_ROLE_ARN,

                Settings={
                    "Inputs": [
                        {
                            "FileInput": input_s3,
                            "AudioSelectors": {
                                "Audio Selector 1": {
                                    "DefaultSelection": "DEFAULT"
                                }
                            },
                            "VideoSelector": {}
                        }
                    ],

                    "OutputGroups": [
                        {
                            "Name": "Apple HLS",
                            "OutputGroupSettings": {
                                "Type": "HLS_GROUP_SETTINGS",
                                "HlsGroupSettings": {
                                    "Destination": output_prefix,
                                    "SegmentLength": 6,
                                    "MinSegmentLength": 0
                                }
                            },

                            "Outputs": [
                                {
                                    "NameModifier": "_1080p",

                                    "ContainerSettings": {
                                        "Container": "M3U8",
                                        "M3u8Settings": {}
                                    },

                                    "VideoDescription": {
                                        "Width": 1920,
                                        "Height": 1080,

                                        "CodecSettings": {
                                            "Codec": "H_264",
                                            "H264Settings": {
                                                "RateControlMode": "QVBR",
                                                "QvbrSettings": {
                                                    "QvbrQualityLevel": 7
                                                },
                                                "MaxBitrate": 4000000
                                            }
                                        }
                                    },

                                    "AudioDescriptions": [
                                        {
                                            "AudioSourceName": "Audio Selector 1",
                                            "CodecSettings": {
                                                "Codec": "AAC",
                                                "AacSettings": {
                                                    "Bitrate": 128000,
                                                    "CodingMode": "CODING_MODE_2_0",
                                                    "SampleRate": 48000
                                                }
                                            }
                                        }
                                    ]
                                },

                                {
                                    "NameModifier": "_720p",

                                    "ContainerSettings": {
                                        "Container": "M3U8",
                                        "M3u8Settings": {}
                                    },

                                    "VideoDescription": {
                                        "Width": 1280,
                                        "Height": 720,

                                        "CodecSettings": {
                                            "Codec": "H_264",
                                            "H264Settings": {
                                                "RateControlMode": "QVBR",
                                                "QvbrSettings": {
                                                    "QvbrQualityLevel": 7
                                                },
                                                "MaxBitrate": 2500000
                                            }
                                        }
                                    },

                                    "AudioDescriptions": [
                                        {
                                            "AudioSourceName": "Audio Selector 1",
                                            "CodecSettings": {
                                                "Codec": "AAC",
                                                "AacSettings": {
                                                    "Bitrate": 128000,
                                                    "CodingMode": "CODING_MODE_2_0",
                                                    "SampleRate": 48000
                                                }
                                            }
                                        }
                                    ]
                                },

                                {
                                    "NameModifier": "_480p",

                                    "ContainerSettings": {
                                        "Container": "M3U8",
                                        "M3u8Settings": {}
                                    },

                                    "VideoDescription": {
                                        "Width": 854,
                                        "Height": 480,

                                        "CodecSettings": {
                                            "Codec": "H_264",
                                            "H264Settings": {
                                                "RateControlMode": "QVBR",
                                                "QvbrSettings": {
                                                    "QvbrQualityLevel": 7
                                                },
                                                "MaxBitrate": 1000000
                                            }
                                        }
                                    },

                                    "AudioDescriptions": [
                                        {
                                            "AudioSourceName": "Audio Selector 1",
                                            "CodecSettings": {
                                                "Codec": "AAC",
                                                "AacSettings": {
                                                    "Bitrate": 96000,
                                                    "CodingMode": "CODING_MODE_2_0",
                                                    "SampleRate": 48000
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            )

            job_id = job["Job"]["Id"]

            video.media_job_id = job_id
            video.status = "processing"
            video.error_message = None
            video.save(
                update_fields=[
                    "media_job_id",
                    "status",
                    "error_message",
                    "updated_at"
                ]
            )

            return CustomResponse.successResponse(
                data={
                    "video_id": str(video.id),
                    "media_job_id": job_id,
                    "status": video.status
                }
            )

        except Exception as e:

            video.status = "failed"
            video.error_message = str(e)
            video.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at"
                ]
            )

            return CustomResponse.errorResponse(
                description=str(e)
            )

class VideoStatusAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            video_id = request.GET.get("video_id", "")
            video = Video.objects.get(id=video_id)
        except Video.DoesNotExist:
            return CustomResponse.errorResponse(
                description="Video not found"
            )

        if not video.media_job_id:
            return CustomResponse.errorResponse(
                description="MediaConvert job not found"
            )

        try:
            mediaconvert = get_media_convert_client()

            response = mediaconvert.get_job(
                Id=video.media_job_id
            )

            job = response["Job"]

            media_status = job["Status"]

            if media_status in ["SUBMITTED", "PROGRESSING"]:
                video.status = "processing"
                video.save(
                    update_fields=[
                        "status",
                        "updated_at"
                    ]
                )

                return CustomResponse.successResponse(
                    data={
                        "video_id": str(video.id),
                        "media_job_id": video.media_job_id,
                        "status": "processing"
                    }
                )

            if media_status == "COMPLETE":

                base_name = os.path.splitext(
                    os.path.basename(video.name)
                )[0]

                hls_key = (
                    f"hls/courses/"
                    f"{video.course_id}/"
                    f"{video.language}/"
                    f"{video.id}/"
                    f"{base_name}.m3u8"
                )

                video.hls_key = hls_key
                video.status = "ready"
                video.error_message = None

                video.save(
                    update_fields=[
                        "hls_key",
                        "status",
                        "error_message",
                        "updated_at"
                    ]
                )

                return CustomResponse.successResponse(
                    data={
                        "video_id": str(video.id),
                        "media_job_id": video.media_job_id,
                        "status": "ready",
                        "hls_key": video.hls_key
                    }
                )

            if media_status == "ERROR":

                error_message = job.get(
                    "ErrorMessage",
                    "MediaConvert job failed"
                )

                video.status = "failed"
                video.error_message = error_message

                video.save(
                    update_fields=[
                        "status",
                        "error_message",
                        "updated_at"
                    ]
                )

                return CustomResponse.successResponse(
                    data={
                        "video_id": str(video.id),
                        "media_job_id": video.media_job_id,
                        "status": "failed",
                        "error_message": error_message
                    }
                )

            return CustomResponse.successResponse(
                data={
                    "video_id": str(video.id),
                    "media_job_id": video.media_job_id,
                    "status": media_status.lower()
                }
            )

        except Exception as e:

            return CustomResponse.errorResponse(
                description=str(e)
            )