from os import getenv
from uuid import uuid4
from typing import Any, Optional, Callable, Dict

from pydantic import BaseModel, Field, ConfigDict, field_validator, PrivateAttr

from phi.utils.log import logger, set_log_level_to_debug


class Workflow(BaseModel):
    # -*- Workflow settings
    # Workflow UUID (autogenerated if not set)
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))

    # -*- Session settings
    # Session UUID (autogenerated if not set)
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    # Session state stored in the database
    session_state: Optional[Dict[str, Any]] = None

    # -*- Workflow Storage
    storage: Optional[Any] = None
    # WorkflowSession from the database: DO NOT SET MANUALLY
    workflow_session: Optional[Any] = None

    # -*- Workflow run details
    # Run ID: do not set manually
    run_id: Optional[str] = None

    # debug_mode=True enables debug logs
    debug_mode: bool = False
    # monitoring=True sends Agent information to phidata.com
    monitoring: bool = getenv("PHI_MONITORING", "false").lower() == "true"
    # telemetry=True logs minimal Agent telemetry on phidata.com
    # This helps us improve the Agent and provide better support
    telemetry: bool = getenv("PHI_TELEMETRY", "true").lower() == "true"

    # The run function provided by the subclass
    _subclass_run: Callable = PrivateAttr()

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    @field_validator("debug_mode")
    def set_log_level(cls, v: bool) -> bool:
        if v:
            set_log_level_to_debug()
            logger.debug("Debug logs enabled")
        return v

    def run(self, *args: Any, **kwargs: Any):
        logger.error(f"{self.__class__.__name__}.run() method not implemented.")
        return

    def run_workflow(self, *args: Any, **kwargs: Any):
        self.run_id = str(uuid4())

        logger.debug(f"*********** Running Workflow: {self.run_id} ***********")
        result = self._subclass_run(*args, **kwargs)
        return result

    def __init__(self, **data):
        super().__init__(**data)
        # Check if 'run' is provided by the subclass
        if self.__class__.run is not Workflow.run:
            # Store the original run method bound to the instance
            self._subclass_run = self.__class__.run.__get__(self)
            # Replace the instance's run method with run_workflow
            object.__setattr__(self, "run", self.run_workflow.__get__(self))
        else:
            # This will log an error when called
            self._subclass_run = self.run
