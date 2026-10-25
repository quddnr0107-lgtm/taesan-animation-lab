# 공개 제작 도구 조사와 실제 접목

| 도구 | 공식 출처 | 확인한 역할 | 이번 상태 |
|---|---|---|---|
| Blender / EEVEE | https://github.com/blender/blender | 메쉬·재질·리그·소프트웨어 렌더링 | 실제 CPU 영상 72프레임 확인; 새 얼굴·연속 머리카락 메쉬 변형 3개 실행 |
| Mesa llvmpipe | https://docs.mesa3d.org/drivers/llvmpipe.html | CPU OpenGL | Actions glxinfo에서 Accelerated:no 확인 |
| Supertonic 3 | https://github.com/supertone-oss-archive/supertonic | 한국어 ONNX CPU TTS | 공식 예제와 고정 모델 revision으로 F1·F4 두 프리셋 실험 |
| Rhubarb Lip Sync | https://github.com/DanielSWolf/rhubarb-lip-sync | 음성에서 입 모양 타이밍 추정 | 공식 v1.14.0 Linux, phonetic 모드 실험; 3D 캐릭터 연결은 다음 단계 |
| TRELLIS.2 | https://github.com/microsoft/TRELLIS.2 | 이미지→3D 자산 생성 | 공식 요구 NVIDIA GPU 24GB 이상. CPU 실험에 실행했다고 주장하지 않음 |
| Hunyuan3D-2 | https://github.com/Tencent-Hunyuan/Hunyuan3D-2 | 이미지→3D 형상·재질 생성 | GPU 경로 후보로 조사. CPU offload를 CPU 단독 실행으로 혼동하지 않음 |
| ComfyUI | https://github.com/Comfy-Org/ComfyUI | 생성 워크플로 API·큐 | 외부 생성 엔진 연결 후보. 현재 CPU 메쉬 실험은 Blender 직접 실행 |

Supertonic 공식 원저자 저장소는 2026-09-09 보관 처리되어 지원이 종료된 상태다. 현재 읽을 수 있는 공식 보관 코드·모델을 실험용으로 사용하고 source SHA, 모델 revision, 의존성과 배포 자산 해시를 남긴다. 재학습·성우 음성 복제는 수행하지 않는다.

새 메쉬 실험은 단순히 도구 목록을 모으는 작업이 아니다. 반복된 구형 머리카락을 연속된 테이퍼 메쉬로 교체하고, 얼굴 버텍스 색으로 볼터치를 섞고, 눈 깊이·홍채·볼과 턱 비율을 A/B/C로 분리해 렌더한다. 같은 카메라·조명 아래 결과를 비교한다. 유사도 백분율을 꾸며내지 않는다.

외부 코드·모델의 사용 조건은 각 공식 배포물에 따른다. 공개 검색·문서 확인과 실제 다운로드·CPU 실행을 구분하며, 목록이 전 세계 모든 도구를 포괄한다고 주장하지 않는다.

## 실행 확인 후 갱신

Supertonic F1·F4 생성, Rhubarb 15구간 추출, Blender B안 실제 입 모양 연결을 완료했다. 3.2083초 영상과 AAC 음성 길이 차이 약 0.0339초. faster-whisper small CPU int8을 별도로 실행해 기대 대본을 프롬프트로 주지 않고 받아썼으며, 문장부호·공백 제외 글자 오류율 0.0을 관측했다.

ASR 공식 소스: https://github.com/SYSTRAN/faster-whisper

[실험 기록과 영구 보관 영상](../results/004-likeness-and-speech.md). 도구 접목 성공과 원본 유사성 달성 여부는 별개이며, 이번 결과는 아직 원본과 동일하지 않다.
