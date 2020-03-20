import os
import uuid
from django.conf import settings
from rest_framework.response import Response
from rest_framework import views, status


class UploadAvatar(views.APIView):
    allow_suffix = ['.jpg', '.png', '.jpeg', '.gif', '.bmp', '.webp']
    dir_name = 'avatar'

    def post(self, request):
        file = request.FILES.get("file", None)
        if file:
            name, suffix = os.path.splitext(file.name)
            if suffix not in self.allow_suffix:
                return Response({'message': '图片格式不支持', 'code': 'format_not_support'}, status=status.HTTP_400_BAD_REQUEST)
            file_name = str(uuid.uuid1()) + suffix
            file_path = os.path.join(settings.MEDIA_ROOT, self.dir_name, file_name)  # 绝对路径
            open(file_path, 'wb').write(file.file.read())  # 写入上传的图片数据
            return Response({"url": os.path.join(self.dir_name, file_name)})
        else:
            Response({'message': '参数异常', 'code': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)
