# Portfolio Summary

## Project

Healthcare GPO Procurement Strategy MVP

## Core Message

기존 Model2의 구매 의사결정 구조를 의료 GPO 구매전략기획 상황에 맞게 경량 재구성했다.

This MVP uses a single-month item-level snapshot dataset. The row unit is decision_month + item_id, which can later be extended into an item-month time-series structure when real historical procurement data becomes available.

## What It Shows

- 카테고리별 구매 데이터 분석
- 원가절감 기회 신호
- 공급망 리스크 신호
- 표준화/대체품/복수소싱 후보
- gate 기반 실행 가능성 검토
- KPI 기반 최종 action 추천

## Connection to Procurement Strategy Planning

| Job Requirement | MVP Implementation | Portfolio Message |
|---|---|---|
| 카테고리별 구매 데이터 분석 | MRO, 진료재료, 장비소모품, 검사재료별 입력 데이터와 상태값 생성 | 카테고리 단위로 구매 이슈를 구조화할 수 있음 |
| 원가절감 기회 발굴 | cost_opportunity_signal과 rebid, annual_contract 후보 생성 | 단가 중심이 아니라 조건과 규모를 함께 보는 절감 기회 분석 |
| KPI 관리 | OTIF, 긴급구매 비중, 표준화, 재고위험, 데이터 품질 지표 사용 | 구매 KPI를 action selection과 연결 |
| 디지털 구매 전환 | CSV 입력부터 최종 추천 파일까지 자동 파이프라인 구성 | 반복 리포트 업무를 데이터 흐름으로 전환 |
| AI 기반 구매 리포트 | rule-based signal과 recommendation output 구성 | 향후 자동 리포트와 분석 보조 기능으로 확장 가능 |
| 공급망 리스크 관리 | supplier_count, supplier_otif, lead_time, inventory risk 기반 신호 생성 | 공급사 집중과 납기 리스크를 조기 식별 |
| 스마트 소싱 전략 | dual_source, review_substitute, standardize_item 후보 생성 | 품목별 소싱 전략 후보를 일관된 기준으로 제안 |
