# 애니메이션 제작 방법·기능 수집 — 2026-10-25

목적: 쫑알쫑알 똘똘이 같은 유아용 3D 애니메이션의 자연스러운 표정·동작·일관성을 목표로 하는 자체 캐릭터 제작 도구. 전 세계 모든 사이트를 조사했다는 뜻은 아니며, 공식 개발사 문서·공개 저장소·모델 배포자의 자료를 확인한 선별 목록이다.

상태: 아래 새 후보는 문서 검토 완료, 설치·추론·품질 검증은 미실행이다. 기존 Blender/Mesa CPU, Supertonic 음성, Rhubarb, faster-whisper 실험 성공과 구분한다. 모델 카드의 속도·품질 주장은 우리 측 측정값이 아니다.

## 우선 가져올 제작 방법

1. **보정 표정:** 눈 감기, 턱 벌리기, 미소를 단순 합산하지 않고, 조합에서 깨지는 모양을 별도 corrective shape로 교정한다. 현재 눈 주변 굴곡과 벌린 입의 모서리가 첫 대상이다.
2. **기준 캐릭터 고정:** 정면·측면·3/4 기준 이미지와 비율표를 확정하고, 동일 모델·재질·리그를 장면마다 재사용한다. 생성 모델로 매 장면 캐릭터를 다시 만들면 일관성 검수가 추가로 필요하다. 이는 본 프로젝트의 설계 판단이다.
3. **몸동작 리타기팅:** 이미 확보한 합법적 동작을 대상 뼈대에 옮기고, 발 접지·손 충돌·어린이 체형에 맞게 교정한다. 기존 단순 사인파 동작을 대체할 후보.
4. **얼굴 캡처와 음성 기반 표정 분리:** 실제 얼굴 영상이 있으면 MediaPipe 계열, 음성만 있으면 audio-to-blendshape 계열을 비교한다. 둘은 서로 다른 입력을 요구한다.
5. **표정 계수와 얼굴 모델 분리:** 52개 표정 계수를 받더라도 얼굴 메시가 그 표정을 표현할 수 있어야 한다. 현재 6개 제어값에 바로 연결한다고 52개 표정 리그가 되지는 않는다.
6. **샷 단위 제작:** 대본→장면 계획→자산 선택→동작/음성/표정→검수용 저해상도→최종 렌더를 분리한다. 실패한 샷만 재실행하는 구성은 본 프로젝트의 설계 제안이다.

## 확인한 도구·기능과 도입 판단

| 후보 / 공식 출처 | 가져올 기능 | CPU 판단 | 도입 조건·실험 |
|---|---|---|---|
| [Blender Studio Rigging](https://studio.blender.org/tools/artist-guide/asset-creation/rigging), [Mouth-open correctives](https://studio.blender.org/training/facial-rigging/mouth-open-corrective-shape-keys/) | 제어 리그 생성, 수동 가중치, 보정 표정의 제작 흐름 | 기존 Blender CPU 제작에 기법 적용 가능 | 우선순위 1. 눈 감기 0/.5/1 × 턱 0/.5/1 × 미소 0/1 조합을 정면·측면 검수. 강좌 전체 무료 접근을 보장하지 않음 |
| [Corrective Smooth](https://docs.blender.org/manual/en/4.2/modeling/modifiers/deform/corrective_smooth.html) | 변형으로 심하게 찌그러진 표면 완화 | Blender 메시 연산 후보 | 눈꺼풀 경계와 눈동자 가림 유지 여부를 함께 검사. 무조건 전체 얼굴에 적용하지 않음 |
| [CloudRig](https://studio.blender.org/tools/addons/cloudrig/introduction), [Pose Shape Keys](https://studio.blender.org/training/blender-studio-rigging-tools/pose-shape-keys/) | 몸·얼굴 제어 리그, 자세별 보정 제작 | Blender 기반 제작 후보 | 현재 Actions Blender 3.0.1과 최신 애드온 호환성은 별도 확인. 최신판을 그대로 설치했다고 주장하지 않음 |
| [Rokoko Blender](https://github.com/Rokoko/rokoko-studio-live-blender), [공식 retarget 가이드](https://support.rokoko.com/hc/en-us/articles/4410463481489-Retarget-an-animation-in-Blender) | 원본 뼈대의 동작을 캐릭터 뼈대로 전달 | 리타기팅은 Blender 연산 후보, 실측 전 | 공식 가이드는 retarget 기능에 프리미엄 계정 불필요 명시. 모션 캡처 서비스·장비·입력 동작의 권리가 모두 무료라는 뜻은 아님. 현재 캐릭터는 먼저 실제 armature 구성이 필요 |
| [MediaPipe Face Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/python) | 영상의 얼굴 랜드마크·표정 계수·변환 행렬 | CPU/웹 실험 후보, 우리 실측 전 | 사람 얼굴 영상 입력용. 음성만으로 표정을 생성하는 도구가 아님. 본인/허용된 연기 영상으로 눈썹·시선·고개 움직임 비교 |
| [LAM Audio2Expression](https://github.com/aigc3d/LAM_Audio2Expression) | 음성에서 ARKit 표정 생성 | 공식 설치 문서는 CUDA 11.8/12.1 경로 | 저장소는 Apache-2.0 표시. 체크포인트와 종속 자산은 별도 확인. CPU 지원으로 단정하지 않음 |
| [Wav2ARKit CPU 배포본](https://huggingface.co/myned-ai/wav2arkit_cpu) | 16kHz 음성→52 ARKit 계수 ONNX | 배포자가 CPUExecutionProvider 예제 제공 | 우선순위 2. 제3자 LAM 파생 배포본. 크기/속도 표기는 미검증이며 외부 가중치 파일·입출력·원본 모델 조건을 확인해야 함. 기존 한국어 WAV와 무음 WAV A/B, 계수 범위·시간축·입 닫힘 검사 |
| [NVIDIA Audio2Face SDK](https://github.com/NVIDIA/Audio2Face-3D-SDK) | 음성→얼굴 연기, 후처리 | 공식 SDK는 CUDA/TensorRT GPU 경로 | GPU 비교 후보. SDK MIT와 모델별 이용 조건은 구분. 일반 CPU Actions의 즉시 대체재로 취급하지 않음 |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) | 메시의 뼈대·스키닝 가중치 예측 | 공식 설치 CUDA/spconv 경로 | 코드 MIT 표시. 공개 체크포인트와 논문 전체 결과의 공개 상태를 구분. 자동 리깅이 얼굴 모델링·의상·표정 보정까지 완성하지 않음 |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | 이미지 기반 3D 자산·텍스처 생성 | 공식 요구 NVIDIA GPU 최소 24GB | 이미지→3D 초안 후보. 최종 애니메이션용 토폴로지·얼굴 내부·리깅이 자동 완성된다는 뜻은 아님 |
| [Wan2.2 Animate](https://github.com/Wan-Video/Wan2.2/blob/main/README.md) | 캐릭터 이미지와 구동 영상으로 애니메이션/교체 영상 생성 | 별도 GPU 경로 | 쇼트 시각 품질 비교 후보. 동일 캐릭터 유지, 손·얼굴 왜곡, 샷 간 연결을 별도 검수. 3D 편집 가능한 리그를 출력하는 방식과 다름 |
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI) | 생성 단계를 노드 그래프로 저장·실행 | CPU 실행판이 있으나 노드·모델마다 다름 | 제작 워크플로 자동화 후보. 자체가 품질 모델은 아니며 CPU 모드가 모든 GPU 모델을 실용 속도로 돌린다는 뜻은 아님 |
| [Poly Haven](https://polyhaven.com/license), [공식 API](https://github.com/Poly-Haven/Public-API) | 배경 소품·PBR 재질·HDRI | 자산 활용은 CPU 렌더 가능, 비용은 복잡도에 좌우 | 자산 CC0 확인. 웹사이트·API 이용 조건은 자산 라이선스와 별도. 필요한 자산만 선택하고 실사 재질을 유아용 톤에 맞게 조정 |

## 다음 실험 순서와 통과 기준

### A. CPU 얼굴 보정 (최우선)
- 새 모델을 매번 생성하지 않고 기존 connected-face에서 보정 모양을 제작.
- 완전 눈 감기뿐 아니라 중간 감기와 미소+턱 벌림 조합을 검사.
- 기준: 눈동자 누출·피부 관통·입 모서리 꺾임·새 경계선 유무를 이미지로 확인. 메시 연결 검사만으로 시각 합격 처리하지 않음.

### B. CPU 음성→표정 후보
- Wav2ARKit 배포 파일의 실제 구성·모델 출처 확인 후 격리된 CPU 작업에서 실행.
- 기존 한국어 음성과 무음 입력을 함께 사용해 랜덤 출력/무음 과동작을 구분.
- 출력 계수를 현 리그의 일부 제어로 매핑하는 시험과, 52개 대응 표정을 실제 제작하는 작업을 구분.
- 출판된 벤치마크를 우리 Actions 성능으로 보고하지 않음.

### C. 몸동작
- Blender armature 구축 후 라이선스가 확인된 동작 하나만 리타기팅.
- 발 미끄러짐·어깨 꺾임·손/몸 관통·어린이 체형에서의 과장 정도를 비교.

### D. 별도 GPU 비교
- TRELLIS.2 / UniRig / Audio2Face / Wan Animate는 CPU 단계와 별도 구성.
- GPU 장비·비용이 확보되지 않은 상태에서 설치·실행 완료로 표시하지 않음.
- 목표는 특정 캐릭터와 동일하다는 주장 대신, 동일 샷의 모델·표정·동작·조명·시간 일관성 차이를 실제 결과로 비교하는 것.

## 현재 결론

우리 실험의 병목은 렌더 해상도보다 캐릭터 자산·표정 구조·연기 데이터다. 따라서 우선순위는 보정 표정 → 음성 표정 후보 검증 → 실제 뼈대와 몸동작 → 샷 자동화다. 이 우선순위는 공식 도구 기능과 현재 결과를 바탕으로 내린 설계 판단이며, 미실행 후보의 품질 보증이 아니다.
