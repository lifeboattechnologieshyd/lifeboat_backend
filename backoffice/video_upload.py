# views.py

import os
import uuid

from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from db.models import Video
from shared.clients.aws.s3 import get_s3_client
from shared.utils import CustomResponse


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