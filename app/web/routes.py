from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

web_router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@web_router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {"request": request})


@web_router.get("/invoices", response_class=HTMLResponse)
async def invoices_page(request: Request):
    return templates.TemplateResponse(request, "invoices.html", {"request": request})


@web_router.get("/hidden-costs", response_class=HTMLResponse)
async def hidden_costs_page(request: Request):
    return templates.TemplateResponse(request, "hidden_costs.html", {"request": request})


@web_router.get("/law", response_class=HTMLResponse)
async def law_page(request: Request):
    return templates.TemplateResponse(request, "law.html", {"request": request})