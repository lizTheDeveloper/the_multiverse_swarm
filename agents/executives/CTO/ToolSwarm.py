import json
import os


class ToolSwarm:
    def __init__(self, model):
        self.model = model
        self.tools_dir = "tools"
        self.tests_dir = "tests"
        os.makedirs(self.tools_dir, exist_ok=True)
        os.makedirs(self.tests_dir, exist_ok=True)


    def request_tools_for_goal(self, goal):
        # Step 1: Plan the tools needed for the goal
        tool_plans_prompt = f"""
        You are a tool planner. Given the following goal, please provide a JSON array of tool plans that would be needed to achieve the goal.
        Each tool plan should include a "name", "description", "inputs", and "outputs" field.

        Goal: {goal}
        """
        tool_plans = self.model.generate_response(tool_plans_prompt)
        tool_plans = json.loads(tool_plans)

        # Step 2: Review the tool plans
        reviewed_tool_plans = []
        for plan in tool_plans:
            review_prompt = f"""
            You are a tool plan reviewer. Given the following tool plan and the associated goal, please review the plan and provide a score between 1 and 5 (where 5 is best) based on how well the plan aligns with and achieves the stated goal.
            
            Goal: {goal}
            
            Tool Plan: {json.dumps(plan)}
            """
            review_score = self.model.generate_response(review_prompt)
            if int(review_score) >= 4:
                reviewed_tool_plans.append(plan)

        # Step 3: Create the approved tools
        created_tools = []
        for tool_plan in reviewed_tool_plans:
            tool = self.request_tool(
                tool_plan["name"],
                tool_plan["description"],
                tool_plan["inputs"],
                tool_plan["outputs"]
            )
            created_tools.append(tool)

        return created_tools

    def request_tool(self, tool_name, tool_description, tool_inputs, tool_outputs):
        # Step 1: Create the initial version of the tool
        create_prompt = f"""
        You are a tool creator. Based on the following specifications, please create a Python function that fulfills the requirements.
        
        Tool Name: {tool_name}
        Description: {tool_description}
        Inputs: {tool_inputs}
        Outputs: {tool_outputs}
        """
        tool_code = self.model.generate_response(create_prompt)

        # Step 2: Review the tool code
        review_prompt = f"""
        You are a tool code reviewer. Given the following tool code and the associated specifications, please review the code and provide feedback on how well it meets the requirements, follows best practices, and any suggestions for improvement.
        
        Tool Name: {tool_name}
        Description: {tool_description}
        Inputs: {tool_inputs}
        Outputs: {tool_outputs}
        
        Tool Code:
        {tool_code}
        """
        review_feedback = self.model.generate_response(review_prompt)

        # Step 3: Revise the tool code based on the review feedback
        revision_prompt = f"""
        You are a tool creator. Given the following tool code and the associated review feedback, please revise the code to address the feedback and improve the implementation.
        
        Original Tool Code:
        {tool_code}
        
        Review Feedback:
        {review_feedback}
        """
        revised_tool_code = self.model.generate_response(revision_prompt)

        # Step 4: Check the alignment of the revised tool
        alignment_prompt = f"""
        You are an AI alignment expert. Given the following tool code and the associated specifications, please analyze the code and provide an assessment of how well it aligns with the intended purpose and any potential misuse or unintended consequences.

        Tool Name: {tool_name}
        Description: {tool_description} 
        Inputs: {tool_inputs}
        Outputs: {tool_outputs}
        
        Revised Tool Code:
        {revised_tool_code}
        """
        alignment_feedback = self.model.generate_response(alignment_prompt)

        # Step 5: If not aligned, repeat steps 3-4 until aligned
        while "not aligned" in alignment_feedback.lower():
            revision_prompt = f"""
            You are a tool creator. Given the following tool code, the associated review feedback, and the alignment feedback, please revise the code to address the feedback and improve the alignment.
            
            Previous Tool Code:
            {revised_tool_code}
            
            Review Feedback:
            {review_feedback}
            
            Alignment Feedback:
            {alignment_feedback}
            """
            revised_tool_code = self.model.generate_response(revision_prompt)
            
            alignment_prompt = f"""
            You are an AI alignment expert. Given the following tool code and the associated specifications, please analyze the code and provide an assessment of how well it aligns with the intended purpose and any potential misuse or unintended consequences.

            Tool Name: {tool_name}
            Description: {tool_description}
            Inputs: {tool_inputs} 
            Outputs: {tool_outputs}
            
            Revised Tool Code:
            {revised_tool_code}
            """
            alignment_feedback = self.model.generate_response(alignment_prompt)

        # Step 6: Save the final aligned tool code
        tool_file = f"{self.tools_dir}/{tool_name}.py"
        with open(tool_file, "w") as f:
            f.write(revised_tool_code)
        
        # Step 7: Generate tests for the tool
        test_prompt = f"""
        You are a test engineer. Given the following tool code and the associated specifications, please write a set of unit tests in Python to verify the functionality and correctness of the tool.

        Tool Name: {tool_name}
        Description: {tool_description}
        Inputs: {tool_inputs}
        Outputs: {tool_outputs}
        
        Tool Code:
        {revised_tool_code}
        """
        test_code = self.model.generate_response(test_prompt)

        # Step 8: Save the test code
        test_file = f"{self.tests_dir}/test_{tool_name}.py"
        with open(test_file, "w") as f:
            f.write(test_code)

        # Step 9: Run the tests
        test_result = self.run_tests(test_file)

        # Step 10: If tests fail, repeat steps 3-9 until tests pass
        while not test_result:
            revision_prompt = f"""
            You are a tool creator. The tests for the tool have failed. Given the following tool code, test code, and the associated specifications, please revise the tool code to make it pass the tests.
            
            Tool Name: {tool_name}
            Description: {tool_description}
            Inputs: {tool_inputs}
            Outputs: {tool_outputs}
            
            Tool Code:
            {revised_tool_code}
            
            Test Code:
            {test_code}
            """
            revised_tool_code = self.model.generate_response(revision_prompt)

            alignment_prompt = f"""
            You are an AI alignment expert. Given the following tool code and the associated specifications, please analyze the code and provide an assessment of how well it aligns with the intended purpose and any potential misuse or unintended consequences.

            Tool Name: {tool_name}
            Description: {tool_description}
            Inputs: {tool_inputs}
            Outputs: {tool_outputs}
            
            Revised Tool Code:
            {revised_tool_code}
            """
            alignment_feedback = self.model.generate_response(alignment_prompt)

            if "not aligned" in alignment_feedback.lower():
                continue

            with open(tool_file, "w") as f:
                f.write(revised_tool_code)

            test_result = self.run_tests(test_file)

        return revised_tool_code

    def run_tests(self, test_file):
        test_result = os.system(f"python {test_file}")
        return test_result == 0