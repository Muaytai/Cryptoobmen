"use client";

import React, {JSX, useState} from "react";

import {PersonalSection} from "@/app/(profile)/profile2/sections/PersonalSection";
import {GiftsSection} from "./sections/GiftsSection";
import {TokensSection} from "./sections/TokensSection";
import {InvestmentsSection} from "./sections/InvestmentsSection/InvestmentsSection";

export const Profile = (): JSX.Element => {

  return (
    <>
      <PersonalSection/>
      <InvestmentsSection/>
      <TokensSection/>
      <GiftsSection/>
    </>
  );
};
