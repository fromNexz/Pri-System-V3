from datetime import date, time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from db import get_connection

router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentCreate(BaseModel):
    name: str = Field(..., example="Cliente Teste")
    phone: str = Field(..., example="5511999999999")
    email: str | None = Field(None, example="cliente@teste.com")
    service_id: int = Field(..., example=5)
    date: date
    start_time: time
    channel: str = Field(..., example="site")  # site, whatsapp


@router.post("/", status_code=201)
def create_appointment(payload: AppointmentCreate):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # 1) Buscar cliente
                cur.execute(
                    """
                    SELECT id, is_blocked
                    FROM customers
                    WHERE phone = %s
                    """,
                    (payload.phone,)
                )
                row = cur.fetchone()

                if row:
                    customer_id = row["id"]
                    is_blocked = row["is_blocked"]
                else:
                    cur.execute(
                        """
                        INSERT INTO customers (name, phone, email, channel)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, is_blocked
                        """,
                        (payload.name, payload.phone,
                         payload.email, payload.channel)
                    )
                    res = cur.fetchone()
                    customer_id = res["id"]
                    is_blocked = res["is_blocked"]

                if is_blocked:
                    raise HTTPException(
                        status_code=403,
                        detail="Cliente bloqueado. Entre em contato com o atendimento."
                    )

                # 3) Criar agendamento
                cur.execute(
                    """
                    INSERT INTO appointments (
                        customer_id,
                        service_id,
                        date,
                        start_time,
                        status,
                        channel,
                        notes,
                        created_by
                    ) VALUES (
                        %s, %s, %s, %s, 'pending', %s, %s, NULL
                    )
                    RETURNING id
                    """,
                    (
                        customer_id,
                        payload.service_id,
                        payload.date,
                        payload.start_time,
                        payload.channel,
                        "Criado via API"
                    )
                )
                appointment = cur.fetchone()
                appointment_id = appointment["id"]

        return {
            "id": appointment_id,
            "customer_id": customer_id,
            "status": "pending"
        }
    finally:
        conn.close()


@router.get("/", response_model=list[dict])
def list_appointments(
    date_filter: Optional[date] = Query(None, alias="date")
):
    """
    Lista agendamentos.
    - Se `date` vier na query (?date=2026-02-20), filtra por dia.
    - Senão, retorna os próximos agendamentos futuros.
    """
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            if date_filter:
                cur.execute(
                    """
                    SELECT a.id,
                           a.customer_id,
                           a.date,
                           a.start_time,
                           a.status,
                           a.channel,
                           c.name AS customer_name,
                           c.phone AS customer_phone,
                           s.name AS service_name
                    FROM appointments a
                    JOIN customers c ON c.id = a.customer_id
                    JOIN services  s ON s.id = a.service_id
                    WHERE a.date = %s
                    ORDER BY a.start_time
                    """,
                    (date_filter,)
                )
            else:
                cur.execute(
                    """
                    SELECT a.id,
                           a.customer_id,
                           a.date,
                           a.start_time,
                           a.status,
                           a.channel,
                           c.name AS customer_name,
                           c.phone AS customer_phone,
                           s.name AS service_name
                    FROM appointments a
                    JOIN customers c ON c.id = a.customer_id
                    JOIN services  s ON s.id = a.service_id
                    WHERE a.date >= CURRENT_DATE
                    ORDER BY a.date, a.start_time
                    LIMIT 100
                    """
                )

            rows = cur.fetchall()
            return rows
    finally:
        conn.close()
