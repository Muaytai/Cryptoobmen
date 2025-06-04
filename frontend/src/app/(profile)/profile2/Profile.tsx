"use client";

import React, {JSX, useState} from "react";

import {DivByAnima} from "./sections/DivByAnima";
import {DivWrapperByAnima} from "./sections/DivWrapperByAnima/DivWrapperByAnima";
import {ViewByAnima} from "./sections/ViewByAnima";
import {ViewWrapperByAnima} from "./sections/ViewWrapperByAnima";

export const Profile = (): JSX.Element => {
  return (
    <>
      <DivByAnima/>
      <DivWrapperByAnima/>
      <ViewWrapperByAnima/>
      <ViewByAnima/>
    </>
  );
};
