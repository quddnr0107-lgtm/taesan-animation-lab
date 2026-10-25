# 010: 도구 소스 실물 수집과 CPU 표정 모델 실행

2026-10-25, 앞서 정리한 후보를 13개 소스/모델 묶음으로 수집했다. 전 세계 전체 사이트·모든 가중치·모든 자산을 받았다는 의미는 아니다.

- [성공한 Actions 실행](https://github.com/quddnr0107-lgtm/taesan-animation-lab/actions/runs/40166724355)
- [압축파일 아티팩트](https://github.com/quddnr0107-lgtm/taesan-animation-lab/actions/runs/40166724355/artifacts/12588508129): 532,258,874 bytes, 2026-11-24 만료
- ZIP SHA-256: c3fefb3b0c2668b2931850e4125da1f3b46c7e51d73723b0e985cbc6d5f72cb9
- [버전·파일·해시 잠금 목록](010-toolkit-manifest.json), [압축파일 내부 파일 검증](010-toolkit-integrity.json), [CPU 실행 결과](010-wav2arkit-cpu.json)

## 받은 내용

Blender Studio 도구/Pose Shape Keys, CloudRig, Blender Corrective Smooth 구현 파일, Rokoko Blender, MediaPipe, LAM Audio2Expression, Wav2ARKit CPU, NVIDIA Audio2Face SDK, UniRig, TRELLIS.2, Wan2.2, ComfyUI, Poly Haven 공식 API 소스.

12개 소스 묶음과 1개 CPU 모델 묶음이다. Corrective Smooth는 별도 플러그인이 아니므로 Blender 전체 배포판 대신 해당 구현 파일과 COPYING/README를 받았다. 다른 소스 아카이브의 submodule·LFS 외부 데이터·사전학습 가중치·설치 의존성까지 자동 확보됐다는 의미는 아니다. Poly Haven은 API 코드이며 전체 자산 라이브러리가 아니다. 소스 내부 저작권·라이선스 파일은 원본 아카이브에 보존됐다. 라이선스 표기 확인과 실제 제품 조합의 이용 가능성 판단은 별개다.

수집 파일은 소스로 보관했으며 외부 저장소의 설치 스크립트는 실행하지 않았다. GPU 도구는 설치·추론 미실행이다.

## CPU 음성 표정 실험

ONNX Runtime 1.23.2 / NumPy 2.2.6 / Python 3.11, CPUExecutionProvider, 2개 intra-op 스레드. 기존 16kHz 모노 한국어 WAV와 같은 길이의 완전 무음 입력을 사용했다.

| 항목 | 실측 |
|---|---:|
| 모델 로드 | 0.4874초 |
| 약 3.174초 한국어 음성 추론 | 0.2554초 |
| 동일 길이 무음 추론 | 0.2409초 |
| 출력 | 1×96×52 표정 계수 |
| 음성/무음 출력 평균 절대 차이 | 0.013899 |
| 프로세스 최대 RSS | 570816 KiB |

단일 짧은 입력의 실측이며 장시간 성능 보장은 아니다. 출력이 유한하고 시간축을 가지며 음성과 무음에 다르게 반응하는 것까지만 검증했다. 한국어 발음 정확도·캐릭터에 적용한 시각 품질은 미검증이다. 무음에서도 최대 0.094 정도의 계수가 나와 별도 무음 보정이 필요하다.

모델 파일은 ONNX 그래프 1,862,753 bytes + 외부 가중치 402,063,360 bytes다. 모델 카드의 1.8MB는 전체 배포 크기가 아니다. 모델 디렉터리 전체 다운로드는 403,977,514 bytes였다.

## 재현

수집 스크립트: tools/collect_animation_toolkit.py. 새 실행 시점의 upstream 최신 커밋을 먼저 확정하고 다운로드 URL·revision·SHA-256을 기록한다.

이번과 동일한 파일은 저장소 루트에서 다음 명령으로 복원한다:

```bash
python tools/restore_animation_toolkit.py --lock results/010-toolkit-manifest.json
```

복원은 URL의 고정 커밋/모델 revision과 SHA-256을 사용하며 외부 코드를 실행하지 않는다. 다운로드 서버 가용성은 별도다.

아티팩트의 숨김 파일 제외 설정 때문에 모델의 .gitattributes 1개는 전송본에 빠졌다. 실행 모델·외부 가중치·README·config·이미지와 모든 소스 아카이브는 존재하고 각각 수집 시 해시와 일치했다. 잠금 목록에는 .gitattributes의 URL/해시도 남아 있어 복원 도구로 추가로 받을 수 있다. 이 Git 메타데이터 누락은 CPU 추론에 영향을 주지 않는다.

다음 통합 대상은 현재 6개 얼굴 제어값과 52개 계수 사이의 매핑·무음 보정이다. 52개 계수가 나왔다는 이유만으로 캐릭터가 52개 표정을 표현한다고 주장하지 않는다.
