import uuid
import logging
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
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
                content={
                    "detail": "Result is not available yet or failed to process."}
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
        <style>
          body {
            background-color: #333333;  /* Darker gray background */
            font-family: Arial, sans-serif;
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;  /* Horizontal center */
            align-items: center;      /* Vertical center */
          }
          .container {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            width: 320px;
          }
          select, input, button {
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 6px;
            box-sizing: border-box;
          }
          button {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
            margin-top: 16px;
          }
          button:hover {
            background-color: #45a049;
          }
          h2 {
            text-align: center;
            color: #333;
            margin-top: 0;
          }
          #result {
            margin-top: 20px;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            color: #333;
            background-color: #f5f5f5;
            border-radius: 6px;
          }
        </style>
        <script>
        function toggleBField() {
          const op = document.getElementById('op').value;
          const bField = document.getElementById('b-field');
          const aInput = document.getElementById('a');
          const bInput = document.getElementById('b');
          
          // Reset inputs when operation changes
          aInput.value = '';
          bInput.value = '';
          
          // Show/hide B field based on operation
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
      <body>
        <div class="container">
          <h2>MathOps Calculator</h2>
          <form onsubmit="submitForm(event)">
            <select id="op" onchange="toggleBField()">
              <option value="pow">Power</option>
              <option value="fib">Fibonacci</option>
              <option value="fact">Factorial</option>
            </select>
            <input id="a" type="number" placeholder="Enter value for A">
            <div id="b-field">
              <input id="b" type="number" placeholder="Enter value for B (power only)">
            </div>
            <button type="submit">Calculate</button>
          </form>
          <div id="result"></div>
        </div>
      </body>
    </html>
    """


@router.get("/db", response_class=HTMLResponse)  
async def view_db(page: int = 1):
    items_per_page = 100
    offset = (page - 1) * items_per_page
    session = SessionLocal()
    
    try:
        # Get total count for pagination
        total_count = session.query(MathOperation).count()
        total_pages = (total_count + items_per_page - 1) // items_per_page

        operations = session.query(MathOperation)\
            .order_by(MathOperation.timestamp.desc())\
            .offset(offset)\
            .limit(items_per_page).all()

        rows_html = ""
        for op in operations:
            timestamp = op.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            rows_html += f"""
                <tr>
                    <td>{op.id}</td>
                    <td class="timestamp">{timestamp}</td>
                    <td>{op.op}</td>
                    <td>{op.a}</td>
                    <td>{op.b if op.b else '-'}</td>
                    <td>{op.result if op.result else 'pending'}</td>
                    <td>{op.status}</td>
                </tr>
            """
        
        # Add pagination controls
        pagination_html = """
            <div class="pagination">
        """
        if page > 1:
            pagination_html += f"""
                <a href="/db?page={page-1}" class="page-btn">Previous</a>
            """
        
        pagination_html += f"""
            <span class="page-info">Page {page} of {total_pages}</span>
        """
        
        if page < total_pages:
            pagination_html += f"""
                <a href="/db?page={page+1}" class="page-btn">Next</a>
            """
        
        pagination_html += "</div>"

        return f"""
        <html>
          <head>
            <title>MathOps DB Viewer</title>
            <style>
                body {{
                    background-color: #333333;
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }}
                .container {{
                    background-color: white;
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                    margin: 0 auto;
                    max-width: 1200px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f5f5f5;
                }}
                h2 {{
                    color: #333;
                    margin-top: 0;
                }}
                .refresh {{
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    float: right;
                }}
                td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                    font-size: 14px;
                }}
                .timestamp {{
                    white-space: nowrap;
                    color: #666;
                }}
                .pagination {{
                    margin-top: 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 20px;
                }}
                .page-btn {{
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    text-decoration: none;
                }}
                .page-btn:hover {{
                    background-color: #45a049;
                }}
                .page-info {{
                    color: #666;
                    font-size: 14px;
                }}
                .table-container {{
                    overflow-x: auto;
                    margin-bottom: 20px;
                }}
            </style>
          </head>
          <body>
            <div class="container">
                <h2>Database Operations
                    <button class="refresh" onclick="location.reload()">Refresh</button>
                </h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Job ID</th>
                                <th>Timestamp</th>
                                <th>Operation</th>
                                <th>A</th>
                                <th>B</th>
                                <th>Result</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
                {pagination_html}
            </div>
          </body>
        </html>
        """
    finally:
        session.close()
