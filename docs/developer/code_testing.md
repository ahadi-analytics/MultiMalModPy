# Testing Guide for MultiMalModPy

This page outlines how we use `pytest` for testing the MultiMalModPy framework.  
It covers **what to test, error handling conventions, and how tests are structured in this repo**.

---

## What to Test
- **Parameter parsing**: CSVs and DataFrames produce the right attributes in experiments.  
- **Invalid inputs**: raise clear exceptions (`ValueError`, `TypeError`, etc.).  
- **Edge cases**: unusual inputs like empty DataFrames or extreme parameter values.  
- **Branch logic**: cover `if`/`else` flows in helpers and input validation.  
- **Scenario replication and combinations**: ensure generated experiments scale correctly.  

---

## Error Handling Conventions
- Raise explicit errors for invalid or impossible input combinations:
  ```python
  def divide(a: float, b: float) -> float:
      if b == 0:
          raise ValueError("Cannot divide by zero")
      return a / b
  ```
- Use guards to avoid parameter combinations that don’t make sense.  
- Validate function inputs before use.  
- Keep error messages descriptive so debugging is straightforward.  

---

## Test Structure in This Repo
- Tests live in the `tests/` folder:
The folder also contains model specific folders to verify model installations and run example jobs.
- `malariasimulation_jobs/`  
  Contains job definitions and scripts for running malaria simulation models.
- `test_EMOD/`  
  Used to test installation and execution of the **EMOD** model.
- `test_malariasimulation/`  
  Used to test installation and execution of the **malariasimulation** model.

  ```
  tests/  
  ├── malariasimulation_jobs/  
  ├── test_EMOD/  
  ├── test_malariasimulation/  
  ├── test_OpenMalaria/  
  ├── test_calibration.py  
  ├── test_helper.py  
  ├── test_helper_local.py  
  └── dummy_experiment.py  
  ```
  
- Fixtures are defined for dummy experiments and scenario DataFrames.   
- `pytest` is used as the main test runner.   
- `unittest.mock.patch` is used to replace external dependencies where needed.  

---

## Example: Parameter Handling
```python
def test_get_param_from_dataframe(dummy_exp, example_scenario_CSV):
    exp_scen_df = example_scenario_CSV[example_scenario_CSV["rownum"] == 0]

    # Overwrite defaults with CSV parameters
    not_param_columns = ["rownum", "exp_name"]
    for col in exp_scen_df.columns:
        if col not in not_param_columns:
            setattr(
                dummy_exp,
                col,
                get_param_from_dataframe(exp_scen_df, col, dummy_exp.sim_params_list),
            )

    assert dummy_exp.seasonality == ["perennial"]
    assert dummy_exp.entomology_mode == "dynamic"
    assert dummy_exp.target_output_name == "eir"
```
This test ensures experiment parameters from a CSV are mapped into the `dummy_exp` object correctly.  

---

## Example: Scenario Replication
```python
def test_rep_scen_df_basic_repetition(basic_scenario_df):
    rep_df = rep_scen_df(basic_scenario_df)

    # 2 rows × 3 seeds = 6 rows expected
    assert len(rep_df) == 6
    assert rep_df["seed"].iloc[0] == 1
    assert rep_df["seed"].iloc[5] == 3
```
This checks that scenario replication logic correctly expands DataFrames by `num_seeds`.

---

## Running Tests
Run all tests:
```bash
pytest
```

Run specific file:
```bash
pytest tests/test_helper.py
```

Run a single test:
```bash
pytest -k test_rep_scen_df_basic_repetition
```

---

## Best Practices
- Keep new tests close to related code (e.g. `test_helper.py` for `utility/helper.py`).  
- Use fixtures for repeatable objects like experiments or example DataFrames.  
- Test both **happy paths** and **failure cases**.  
- Patch external dependencies (e.g. interventions, manifest) so tests stay fast and isolated.  
- Keep tests small and focused.  
