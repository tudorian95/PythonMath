import uuid
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from schemas import MathRequest, MathResponse, MathResult
from workers import queue
from db import SessionLocal
from models import MathOperation

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/calculate", response_model=MathResponse)
async def calculate(req: MathRequest):
    job_id = str(uuid.uuid4())
    session = SessionLocal()
    try:
        db_entry = MathOperation(id=job_id, op=req.op, a=req.a, b=req.b)
        session.add(db_entry)
        session.commit()
        logger.info(f"Task added to database with job_id: {job_id}")
    except OverflowError:
        session.rollback()
        return JSONResponse(
            status_code=400,
            content={"detail": "Result too large to process."}
        )
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding task to database: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Unexpected error: {str(e)}"}
        )
    finally:
        session.close()

    await queue.put({"op": req.op, "a": req.a, "b": req.b, "job_id": job_id})
    logger.info(f"Task added to queue with job_id: {job_id}")
    return {"job_id": job_id}

@router.get("/result/{job_id}", response_model=MathResult)
async def get_result(job_id: str):
    session = SessionLocal()
    try:
        op = session.query(MathOperation).filter_by(id=job_id).first()
        if not op:
            return JSONResponse(
                status_code=404,
                content={"detail": "Job ID not found"}
            )
        if op.result is None:
            return JSONResponse(
                status_code=500,
                content={"detail": "Result is not available yet or failed to process."}
            )
        return {
            "result": str(op.result),  # Convert result to string
            "status": op.status
        }
    except Exception as e:
        logger.error(f"Error fetching result for job_id {job_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Unexpected error: {str(e)}"}
        )
    finally:
        session.close()

@router.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    return """
    <html>
      <head>
        <title>MathOps UI</title>
        <script>
        function toggleBField() {
          const op = document.getElementById('op').value;
          const bField = document.getElementById('b-field');
          bField.style.display = op === 'pow' ? 'block' : 'none';
        }

        async function submitForm(e) {
          e.preventDefault();
          const op = document.getElementById('op').value;
          const a = parseInt(document.getElementById('a').value);
          const bInput = document.getElementById('b');
          const b = parseInt(bInput.value);
          const resDiv = document.getElementById('result');

          if (isNaN(a) || (op === 'pow' && isNaN(b))) {
            resDiv.innerText = 'Invalid input: A is required, and B is required for power.';
            return;
          }

          resDiv.innerText = 'Submitting...';

          const payload = { op, a };
          if (op === 'pow') payload.b = b;

          try {
            const calcResp = await fetch('/calculate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            });

            if (!calcResp.ok) {
              let errMessage = 'Request failed';
              try {
                const err = await calcResp.json();
                errMessage = err.detail || errMessage;
              } catch (parseError) {
                errMessage = 'Unexpected response from server.';
              }
              resDiv.innerText = 'Error: ' + errMessage;
              return;
            }

            const { job_id } = await calcResp.json();

            let tries = 0;
            const poll = setInterval(async () => {
              try {
                const resultResp = await fetch(`/result/${job_id}`);

                if (!resultResp.ok) {
                  clearInterval(poll);
                  let errMessage = 'Unknown error';
                  try {
                    const err = await resultResp.json();
                    errMessage = err.detail || errMessage;
                  } catch (parseError) {
                    errMessage = 'Unexpected response from server.';
                  }
                  resDiv.innerText = 'Error while polling result: ' + errMessage;
                  return;
                }

                const data = await resultResp.json();

                if (data.status === 'done') {
                  clearInterval(poll);
                  resDiv.innerText = 'Result: ' + data.result;
                } else if (data.status === 'failed') {
                  clearInterval(poll);
                  resDiv.innerText = 'Error: ' + data.result;
                } else if (++tries > 20) {
                  clearInterval(poll);
                  resDiv.innerText = 'Timed out waiting for result.';
                }
              } catch (err) {
                clearInterval(poll);
                resDiv.innerText = 'Polling error: ' + err.message;
              }
            }, 1000);
          } catch (err) {
            resDiv.innerText = 'Unexpected error occurred: ' + err.message;
          }
        }
        </script>
      </head>
      <body onload="toggleBField()">
        <h2>MathOps Web UI</h2>
        <form onsubmit="submitForm(event)">
          <label>Operation:</label>
          <select id="op" onchange="toggleBField()">
            <option value="pow">Power</option>
            <option value="fib">Fibonacci</option>
            <option value="fact">Factorial</option>
          </select><br><br>

          <label>A:</label><input id="a" type="number"><br><br>

          <div id="b-field">
            <label>B (for pow):</label><input id="b" type="number"><br><br>
          </div>

          <button type="submit">Submit</button>
        </form>
        <h3 id="result"></h3>
      </body>
    </html>
    """