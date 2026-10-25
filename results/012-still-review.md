# 012: CPU 정지 장면 검수

[실제 대표 장면](012-hero.png) · [눈 감은 장면](012-blink.png)

실행 40175412638 성공, 960×540 두 장면, 렌더 87.78초. 앞선 40174636974는 Filmic 미지원으로 실패했고 지원되는 Standard 변환으로 재실행했다. 원시 report의 changes 배열에 남은 'Filmic color management'는 부정확하며, 실제 적용값은 color_transform=Standard, color_look=None이다.

시각 검수: 얼굴과 배경은 밝아졌고 입 안쪽 표현이 추가됐다. 다만 얼굴과 손 하이라이트가 지나치게 밝고, 닫힌 눈꺼풀은 두껍게 돌출되며 눈 밑 그림자가 남는다. 머리카락과 얼굴 비율도 생성한 목표 이미지에 도달하지 못했다. 전체 영상은 아직 렌더하지 않았고 animation_frames=0이다. 이 결과를 Gemini 수준이나 목표 이미지의 동영상화로 제시하지 않는다.

별도 이미지 생성 도구로 만든 목표 이미지는 assets/quality-target-v1.png이며 실제 CPU 렌더와 구분한다. Runway는 사용하지 않았다.
