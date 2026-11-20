from app.core.jobs import JobQueue


def test_jobs_run_in_order_and_record_results():
    q = JobQueue()
    order = []
    a = q.submit("x", 1, lambda: order.append("a") or 1)
    b = q.submit("x", 1, lambda: order.append("b") or 2)
    q.join()
    assert order == ["a", "b"]
    assert (a.status, a.result, b.result) == ("done", 1, 2)
    assert q.get(a.id).finished is not None
    q.shutdown()


def test_failed_job_keeps_worker_alive():
    q = JobQueue()
    bad = q.submit("x", 1, lambda: 1 / 0)
    good = q.submit("x", 1, lambda: "ok")
    q.join()
    assert bad.status == "failed" and "division" in bad.error
    assert good.status == "done"
    q.shutdown()


def test_old_finished_jobs_are_pruned():
    q = JobQueue(max_kept=2)
    jobs = [q.submit("x", 1, lambda: None) for _ in range(3)]
    q.join()
    q.submit("x", 1, lambda: None)
    q.join()
    assert q.get(jobs[0].id) is None
    q.shutdown()
